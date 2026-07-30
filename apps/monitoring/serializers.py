"""
Serializers for monitoring app.
"""
from rest_framework import serializers
from .models import VitalSign, Symptom, RiskScore, Notification, ClinicalAlert


class ClinicalAlertSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ClinicalAlert
        fields = [
            'id', 'patient', 'patient_name',
            'condition_name', 'severity', 'severity_display',
            'reason', 'guidance',
            'symptoms_used', 'vital_signs_used',
            'related_vital_sign', 'related_symptom',
            'status', 'status_display',
            'viewed',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'patient', 'condition_name', 'severity',
            'reason', 'guidance', 'symptoms_used', 'vital_signs_used',
            'related_vital_sign', 'related_symptom', 'created_at', 'updated_at',
        ]



class VitalSignSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.name', read_only=True)

    class Meta:
        model = VitalSign
        fields = [
            'id', 'patient', 'patient_name',
            'systolic_bp', 'diastolic_bp', 'heart_rate',
            'temperature_celsius', 'weight_kg', 'oxygen_saturation',
            'blood_glucose', 'notes', 'recorded_at', 'synced', 'created_at',
        ]
        read_only_fields = ['id', 'patient', 'created_at']

    def validate(self, attrs):
        # Validate at least one measurement is provided
        measurement_fields = [
            'systolic_bp', 'diastolic_bp', 'heart_rate',
            'temperature_celsius', 'weight_kg', 'oxygen_saturation', 'blood_glucose'
        ]
        if not any(attrs.get(f) for f in measurement_fields):
            raise serializers.ValidationError(
                'Pelo menos uma medição deve ser fornecida.'
            )

        # Validate blood pressure coherence
        sys_bp = attrs.get('systolic_bp')
        dia_bp = attrs.get('diastolic_bp')
        if sys_bp and dia_bp and sys_bp <= dia_bp:
            raise serializers.ValidationError(
                {'systolic_bp': 'A pressão sistólica deve ser maior que a diastólica.'}
            )

        # Validate oxygen saturation range
        spo2 = attrs.get('oxygen_saturation')
        if spo2 and not (0 <= spo2 <= 100):
            raise serializers.ValidationError(
                {'oxygen_saturation': 'Saturação deve estar entre 0 e 100%.'}
            )

        return attrs


class SymptomSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    symptom_type_display = serializers.CharField(source='get_symptom_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)

    class Meta:
        model = Symptom
        fields = [
            'id', 'patient', 'patient_name',
            'symptom_type', 'symptom_type_display',
            'severity', 'severity_display',
            'description', 'duration_hours',
            'recorded_at', 'synced', 'created_at',
        ]
        read_only_fields = ['id', 'patient', 'created_at']


class RiskScoreSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    risk_level_display = serializers.CharField(source='get_risk_level_display', read_only=True)

    class Meta:
        model = RiskScore
        fields = [
            'id', 'patient', 'patient_name',
            'score', 'risk_level', 'risk_level_display',
            'contributing_factors', 'calculated_at',
        ]
        read_only_fields = [
            'id', 'patient', 'score', 'risk_level',
            'contributing_factors', 'calculated_at',
        ]


class NotificationSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    clinical_alert_id = serializers.PrimaryKeyRelatedField(
        source='clinical_alert', read_only=True
    )

    class Meta:
        model = Notification
        fields = [
            'id', 'patient', 'patient_name',
            'notification_type', 'notification_type_display',
            'severity', 'severity_display',
            'title', 'message',
            'vital_sign', 'symptom', 'risk_score',
            'clinical_alert_id',
            'read',
            'created_at',
        ]
        read_only_fields = [
            'id', 'patient', 'notification_type', 'severity', 'title', 'message',
            'vital_sign', 'symptom', 'risk_score', 'clinical_alert_id', 'created_at'
        ]


class DashboardSerializer(serializers.Serializer):
    """
    Serializer for the doctor's clinical dashboard overview.
    """
    patient_id = serializers.IntegerField()
    patient_name = serializers.CharField()
    gestational_age_weeks = serializers.IntegerField(allow_null=True)
    latest_risk_score = RiskScoreSerializer(allow_null=True)
    latest_vital_signs = VitalSignSerializer(allow_null=True)
    unread_alerts_count = serializers.IntegerField()
    last_activity = serializers.DateTimeField(allow_null=True)
