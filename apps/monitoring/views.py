"""
Views for monitoring app — vital signs, symptoms, risk scores, alerts, dashboard.
"""
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

_TAG = ['monitoring']

from apps.accounts.permissions import IsPatient, IsValidatedDoctor, IsOwnerOrDoctor
from .models import VitalSign, Symptom, RiskScore, Alert
from .serializers import (
    VitalSignSerializer, SymptomSerializer,
    RiskScoreSerializer, AlertSerializer, DashboardSerializer,
)
from .services import calculate_risk_score, check_and_create_alerts


# ─────────────────────────────────────────────
# Vital Signs
# ─────────────────────────────────────────────

@extend_schema_view(
    get=extend_schema(tags=_TAG, summary='Listar Sinais Vitais', description='Paciente: próprios registros. Médico: sinais das pacientes vinculadas.'),
    post=extend_schema(tags=_TAG, summary='[Paciente] Registrar Sinal Vital', description='Registra um novo sinal vital. O sistema calcula automaticamente o score de risco e gera alertas se necessário.'),
)
class VitalSignListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/monitoring/vital-signs/   — patient sees own; doctor sees linked patients
    POST /api/monitoring/vital-signs/   — patient registers new vital sign
    """
    serializer_class = VitalSignSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsPatient()]
        return [IsAuthenticated()]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return VitalSign.objects.none()
        user = self.request.user
        if user.is_patient:
            return VitalSign.objects.filter(patient=user)
        elif user.is_doctor:
            # Doctor sees vital signs of linked patients
            try:
                doctor = user.doctor_profile
                patient_ids = doctor.patients.values_list('user_id', flat=True)
                return VitalSign.objects.filter(patient_id__in=patient_ids)
            except Exception:
                return VitalSign.objects.none()
        return VitalSign.objects.none()

    def perform_create(self, serializer):
        vital_sign = serializer.save(patient=self.request.user)
        # Auto-calculate risk score
        result = calculate_risk_score(vital_sign=vital_sign, patient=self.request.user)
        risk_score_obj = RiskScore.objects.create(
            patient=self.request.user,
            score=result['score'],
            risk_level=result['risk_level'],
            contributing_factors=result['contributing_factors'],
        )
        # Generate alerts if needed
        check_and_create_alerts(
            vital_sign=vital_sign,
            patient=self.request.user,
            risk_score_obj=risk_score_obj,
        )


@extend_schema(tags=_TAG, summary='Detalhe de Sinal Vital')
class VitalSignDetailView(generics.RetrieveAPIView):
    """
    GET /api/monitoring/vital-signs/{id}/
    """
    serializer_class = VitalSignSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrDoctor]

    def get_queryset(self):
        # Guard for schema generation (drf-spectacular)
        if getattr(self, 'swagger_fake_view', False):
            return VitalSign.objects.none()
        user = self.request.user
        if user.is_patient:
            return VitalSign.objects.filter(patient=user)
        elif user.is_doctor:
            try:
                doctor = user.doctor_profile
                patient_ids = doctor.patients.values_list('user_id', flat=True)
                return VitalSign.objects.filter(patient_id__in=patient_ids)
            except Exception:
                return VitalSign.objects.none()
        return VitalSign.objects.none()


# ─────────────────────────────────────────────
# Symptoms
# ─────────────────────────────────────────────

@extend_schema_view(
    get=extend_schema(tags=_TAG, summary='Listar Sintomas', description='Paciente: próprios registros. Médico: sintomas das pacientes vinculadas.'),
    post=extend_schema(tags=_TAG, summary='[Paciente] Registrar Sintoma', description='Registra um novo sintoma gestacional. Reavalia automaticamente o score de risco.'),
)
class SymptomListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/monitoring/symptoms/  — patient sees own; doctor sees linked patients
    POST /api/monitoring/symptoms/  — patient registers a new symptom
    """
    serializer_class = SymptomSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsPatient()]
        return [IsAuthenticated()]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Symptom.objects.none()
        user = self.request.user
        if user.is_patient:
            return Symptom.objects.filter(patient=user)
        elif user.is_doctor:
            try:
                doctor = user.doctor_profile
                patient_ids = doctor.patients.values_list('user_id', flat=True)
                return Symptom.objects.filter(patient_id__in=patient_ids)
            except Exception:
                return Symptom.objects.none()
        return Symptom.objects.none()

    def perform_create(self, serializer):
        symptom = serializer.save(patient=self.request.user)
        # Recalculate risk score
        result = calculate_risk_score(symptom=symptom, patient=self.request.user)
        risk_score_obj = RiskScore.objects.create(
            patient=self.request.user,
            score=result['score'],
            risk_level=result['risk_level'],
            contributing_factors=result['contributing_factors'],
        )
        check_and_create_alerts(
            symptom=symptom,
            patient=self.request.user,
            risk_score_obj=risk_score_obj,
        )


# ─────────────────────────────────────────────
# Risk Score
# ─────────────────────────────────────────────

@extend_schema(tags=_TAG, summary='Histórico de Score de Risco', description='Retorna o histórico de scores de risco. Paciente vê o próprio; médico pode filtrar por patient_id.')
class RiskScoreListView(generics.ListAPIView):
    """
    GET /api/monitoring/risk-score/
    Patient: own risk score history
    Doctor: risk scores of linked patients (optionally filtered by patient_id)
    """
    serializer_class = RiskScoreSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return RiskScore.objects.none()
        user = self.request.user
        if user.is_patient:
            return RiskScore.objects.filter(patient=user)
        elif user.is_doctor:
            try:
                doctor = user.doctor_profile
                patient_ids = doctor.patients.values_list('user_id', flat=True)
                qs = RiskScore.objects.filter(patient_id__in=patient_ids)
                patient_id = self.request.query_params.get('patient_id')
                if patient_id:
                    qs = qs.filter(patient_id=patient_id)
                return qs
            except Exception:
                return RiskScore.objects.none()
        return RiskScore.objects.none()


@extend_schema(tags=_TAG, summary='Último Score de Risco', description='Retorna apenas o score de risco mais recente. Médico deve informar ?patient_id=.')
class LatestRiskScoreView(APIView):
    """
    GET /api/monitoring/risk-score/latest/
    Returns only the latest risk score.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            if user.is_patient:
                score = RiskScore.objects.filter(patient=user).latest()
            elif user.is_doctor:
                patient_id = request.query_params.get('patient_id')
                if not patient_id:
                    return Response({'error': 'patient_id é obrigatório para médicos.'}, status=400)
                score = RiskScore.objects.filter(patient_id=patient_id).latest()
            else:
                return Response(status=status.HTTP_403_FORBIDDEN)

            return Response(RiskScoreSerializer(score).data)
        except RiskScore.DoesNotExist:
            return Response({'message': 'Nenhum score calculado ainda.'}, status=404)


# ─────────────────────────────────────────────
# Alerts
# ─────────────────────────────────────────────

@extend_schema(tags=_TAG, summary='Listar Alertas', description='Alertas clínicos gerados automaticamente pelo sistema. Filtrável por alert_type, severity e read_by_patient.')
class AlertListView(generics.ListAPIView):
    """
    GET /api/monitoring/alerts/
    Patients see own alerts. Doctors see alerts of linked patients.
    """
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['alert_type', 'severity', 'read_by_patient']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Alert.objects.none()
        user = self.request.user
        if user.is_patient:
            return Alert.objects.filter(patient=user)
        elif user.is_doctor:
            try:
                doctor = user.doctor_profile
                patient_ids = doctor.patients.values_list('user_id', flat=True)
                return Alert.objects.filter(patient_id__in=patient_ids)
            except Exception:
                return Alert.objects.none()
        return Alert.objects.none()


@extend_schema(tags=_TAG, summary='Marcar Alerta como Lido')
class MarkAlertReadView(APIView):
    """
    POST /api/monitoring/alerts/{id}/read/
    Mark an alert as read.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        try:
            alert = Alert.objects.get(pk=pk)
        except Alert.DoesNotExist:
            return Response({'error': 'Alerta não encontrado.'}, status=404)

        if user.is_patient and alert.patient == user:
            alert.read_by_patient = True
            alert.save(update_fields=['read_by_patient'])
        elif user.is_doctor:
            try:
                doctor = user.doctor_profile
                if alert.patient.patient_profile.doctor == doctor:
                    alert.read_by_doctor = True
                    alert.save(update_fields=['read_by_doctor'])
                else:
                    return Response(status=status.HTTP_403_FORBIDDEN)
            except Exception:
                return Response(status=status.HTTP_403_FORBIDDEN)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)

        return Response({'message': 'Alerta marcado como lido.'})


# ─────────────────────────────────────────────
# Clinical Dashboard (Doctor only)
# ─────────────────────────────────────────────

@extend_schema(
    tags=_TAG,
    summary='[Médico] Dashboard Clínico',
    description='Visão geral de todas as pacientes vinculadas, ordenadas por nível de risco e alertas não lidos. Requer CRM validado.',
    responses={200: DashboardSerializer(many=True)},
)
class ClinicalDashboardView(APIView):
    """
    GET /api/monitoring/dashboard/
    Doctor-only overview: all linked patients with latest data.
    """
    def get_permissions(self):
        return [IsValidatedDoctor()]

    def get(self, request):
        doctor = request.user.doctor_profile
        patients = doctor.patients.select_related('user').all()

        dashboard_data = []
        for patient_profile in patients:
            patient_user = patient_profile.user
            try:
                latest_score = RiskScore.objects.filter(patient=patient_user).latest()
            except RiskScore.DoesNotExist:
                latest_score = None

            try:
                latest_vitals = VitalSign.objects.filter(patient=patient_user).latest('recorded_at')
            except VitalSign.DoesNotExist:
                latest_vitals = None

            unread_alerts = Alert.objects.filter(
                patient=patient_user, read_by_doctor=False
            ).count()

            # Last activity: most recent vital sign or symptom
            last_vital_at = getattr(latest_vitals, 'recorded_at', None)
            last_symptom = Symptom.objects.filter(patient=patient_user).order_by('-recorded_at').first()
            last_symptom_at = getattr(last_symptom, 'recorded_at', None)

            if last_vital_at and last_symptom_at:
                last_activity = max(last_vital_at, last_symptom_at)
            else:
                last_activity = last_vital_at or last_symptom_at

            dashboard_data.append({
                'patient_id': patient_user.id,
                'patient_name': patient_user.name,
                'gestational_age_weeks': patient_profile.gestational_age_weeks,
                'latest_risk_score': RiskScoreSerializer(latest_score).data if latest_score else None,
                'latest_vital_signs': VitalSignSerializer(latest_vitals).data if latest_vitals else None,
                'unread_alerts_count': unread_alerts,
                'last_activity': last_activity,
            })

        # Sort by risk level and unread alerts
        dashboard_data.sort(
            key=lambda x: (
                -(x['latest_risk_score']['score'] if x['latest_risk_score'] else 0),
                -x['unread_alerts_count'],
            )
        )
        return Response(dashboard_data)


@extend_schema(tags=_TAG, summary='[Médico] Timeline da Paciente', description='Timeline cronológica dos sinais vitais, sintomas e scores de uma paciente. Requer ?patient_id=.')
class PatientTimelineView(APIView):
    """
    GET /api/monitoring/timeline/?patient_id=<id>
    Doctor-only: chronological timeline of a patient's vital signs and symptoms.
    """
    def get_permissions(self):
        return [IsValidatedDoctor()]

    def get(self, request):
        patient_id = request.query_params.get('patient_id')
        if not patient_id:
            return Response({'error': 'patient_id é obrigatório.'}, status=400)

        # Ensure the patient is linked to this doctor
        doctor = request.user.doctor_profile
        patient_ids = doctor.patients.values_list('user_id', flat=True)
        if int(patient_id) not in patient_ids:
            return Response(status=status.HTTP_403_FORBIDDEN)

        vital_signs = VitalSign.objects.filter(patient_id=patient_id).order_by('-recorded_at')[:50]
        symptoms = Symptom.objects.filter(patient_id=patient_id).order_by('-recorded_at')[:50]
        risk_scores = RiskScore.objects.filter(patient_id=patient_id).order_by('-calculated_at')[:50]

        return Response({
            'vital_signs': VitalSignSerializer(vital_signs, many=True).data,
            'symptoms': SymptomSerializer(symptoms, many=True).data,
            'risk_scores': RiskScoreSerializer(risk_scores, many=True).data,
        })
