"""
Serializers for consultations app.
"""
from django.utils import timezone
from rest_framework import serializers
from .models import Consultation, Prescription, ExamRequest


class ConsultationSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    consultation_type_display = serializers.CharField(source='get_consultation_type_display', read_only=True)

    class Meta:
        model = Consultation
        fields = [
            'id', 'patient', 'patient_name', 'doctor', 'doctor_name',
            'scheduled_date', 'consultation_type', 'consultation_type_display',
            'location', 'status', 'status_display', 'notes',
            'cancellation_reason', 'cancelled_at',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'patient', 'doctor', 'status', 'cancellation_reason', 'cancelled_at', 'created_at', 'updated_at']

    def validate_scheduled_date(self, value):
        if value < timezone.now():
            raise serializers.ValidationError('A data da consulta deve ser no futuro.')
        return value


class ConsultationCreateSerializer(serializers.ModelSerializer):
    """Used by doctors to create consultations."""
    class Meta:
        model = Consultation
        fields = [
            'patient', 'scheduled_date', 'consultation_type',
            'location', 'notes',
        ]

    def validate_scheduled_date(self, value):
        if value < timezone.now():
            raise serializers.ValidationError('A data da consulta deve ser no futuro.')
        return value

    def validate_patient(self, patient):
        """Ensure the patient is linked to the requesting doctor."""
        request = self.context.get('request')
        if request and request.user.is_doctor:
            try:
                doctor = request.user.doctor_profile
                if not doctor.patients.filter(user=patient).exists():
                    raise serializers.ValidationError(
                        'Esta paciente não está vinculada ao seu acompanhamento.'
                    )
            except Exception:
                raise serializers.ValidationError('Erro ao validar paciente.')
        return patient


class CancelConsultationSerializer(serializers.Serializer):
    reason = serializers.CharField(
        required=False, allow_blank=True,
        max_length=500, default='',
        label='Motivo do cancelamento'
    )


class PrescriptionSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)
    prescription_type_display = serializers.CharField(source='get_prescription_type_display', read_only=True)

    class Meta:
        model = Prescription
        fields = [
            'id', 'patient', 'patient_name', 'doctor', 'doctor_name',
            'consultation', 'prescription_type', 'prescription_type_display',
            'title', 'content', 'instructions', 'valid_until',
            'digital_signature', 'issued_at', 'created_at',
        ]
        read_only_fields = ['id', 'doctor', 'digital_signature', 'issued_at', 'created_at']


class PrescriptionCreateSerializer(serializers.ModelSerializer):
    """Used by doctors to issue prescriptions."""
    class Meta:
        model = Prescription
        fields = [
            'patient', 'consultation', 'prescription_type',
            'title', 'content', 'instructions', 'valid_until',
        ]

    def validate_patient(self, patient):
        request = self.context.get('request')
        if request and request.user.is_doctor:
            try:
                doctor = request.user.doctor_profile
                if not doctor.patients.filter(user=patient).exists():
                    raise serializers.ValidationError(
                        'Esta paciente não está vinculada ao seu acompanhamento.'
                    )
            except Exception:
                raise serializers.ValidationError('Erro ao validar paciente.')
        return patient


class ExamRequestSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ExamRequest
        fields = [
            'id', 'patient', 'patient_name', 'doctor', 'doctor_name',
            'consultation', 'exam_name', 'clinical_indication',
            'priority', 'priority_display', 'status', 'status_display',
            'notes', 'result_notes', 'requested_at', 'created_at',
        ]
        read_only_fields = ['id', 'doctor', 'status', 'requested_at', 'created_at']


class ExamRequestCreateSerializer(serializers.ModelSerializer):
    """Used by doctors to issue exam requests."""
    class Meta:
        model = ExamRequest
        fields = [
            'patient', 'consultation', 'exam_name',
            'clinical_indication', 'priority', 'notes',
        ]

    def validate_patient(self, patient):
        request = self.context.get('request')
        if request and request.user.is_doctor:
            try:
                doctor = request.user.doctor_profile
                if not doctor.patients.filter(user=patient).exists():
                    raise serializers.ValidationError(
                        'Esta paciente não está vinculada ao seu acompanhamento.'
                    )
            except Exception:
                raise serializers.ValidationError('Erro ao validar paciente.')
        return patient
