"""
Views for consultations app.
"""
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsPatient, IsValidatedDoctor
from .models import Consultation, Prescription, ExamRequest
from .serializers import (
    ConsultationSerializer, ConsultationCreateSerializer, CancelConsultationSerializer,
    PrescriptionSerializer, PrescriptionCreateSerializer,
    ExamRequestSerializer, ExamRequestCreateSerializer,
)

_TAG = ['consultations']


# ─────────────────────────────────────────────
# Consultations
# ─────────────────────────────────────────────

@extend_schema_view(
    get=extend_schema(tags=_TAG, summary='Listar Consultas', description='Paciente: próprias consultas. Médico: agenda de consultas.'),
    post=extend_schema(tags=_TAG, summary='[Médico] Agendar Consulta', description='Agenda uma nova consulta para uma paciente vinculada. Requer CRM validado.'),
)
class ConsultationListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/consultations/         — list consultations (patient: own; doctor: own schedule)
    POST /api/consultations/         — doctor schedules a consultation
    """
    filterset_fields = ['status', 'consultation_type']

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsValidatedDoctor()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ConsultationCreateSerializer
        return ConsultationSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_patient:
            return Consultation.objects.filter(patient=user).select_related('doctor')
        elif user.is_doctor:
            return Consultation.objects.filter(doctor=user).select_related('patient')
        return Consultation.objects.none()

    def perform_create(self, serializer):
        serializer.save(doctor=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # Return full representation
        consultation = serializer.instance
        return Response(
            ConsultationSerializer(consultation).data,
            status=status.HTTP_201_CREATED
        )


@extend_schema_view(
    get=extend_schema(tags=_TAG, summary='Detalhe de Consulta'),
    patch=extend_schema(tags=_TAG, summary='[Médico] Atualizar Consulta'),
)
class ConsultationDetailView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/consultations/{id}/  — get consultation detail
    PATCH /api/consultations/{id}/  — doctor updates notes/type/date
    """
    serializer_class = ConsultationSerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH']:
            return [IsValidatedDoctor()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.is_patient:
            return Consultation.objects.filter(patient=user)
        elif user.is_doctor:
            return Consultation.objects.filter(doctor=user)
        return Consultation.objects.none()


@extend_schema(tags=_TAG, summary='Cancelar Consulta', description='Paciente ou Médico pode cancelar uma consulta. Informe o motivo opcionalmente.')
class CancelConsultationView(APIView):
    """
    POST /api/consultations/{id}/cancel/
    Both patient and validated doctor can cancel.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        user = request.user

        # Get the consultation
        if user.is_patient:
            try:
                consultation = Consultation.objects.get(pk=pk, patient=user)
            except Consultation.DoesNotExist:
                return Response({'error': 'Consulta não encontrada.'}, status=404)
        elif user.is_doctor:
            try:
                consultation = Consultation.objects.get(pk=pk, doctor=user)
            except Consultation.DoesNotExist:
                return Response({'error': 'Consulta não encontrada.'}, status=404)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)

        if consultation.status == Consultation.Status.CANCELLED:
            return Response({'error': 'Consulta já está cancelada.'}, status=400)

        if consultation.status == Consultation.Status.COMPLETED:
            return Response({'error': 'Consulta já foi realizada.'}, status=400)

        serializer = CancelConsultationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        consultation.cancel(cancelled_by=user, reason=serializer.validated_data.get('reason', ''))

        return Response({
            'message': 'Consulta cancelada com sucesso.',
            'consultation': ConsultationSerializer(consultation).data,
        })


# ─────────────────────────────────────────────
# Prescriptions
# ─────────────────────────────────────────────

@extend_schema_view(
    get=extend_schema(tags=_TAG, summary='Listar Receitas'),
    post=extend_schema(tags=_TAG, summary='[Médico] Emitir Receita Digital', description='Emite uma receita digital para uma paciente vinculada. Requer CRM validado.'),
)
class PrescriptionListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/consultations/prescriptions/  — patient: own; doctor: issued
    POST /api/consultations/prescriptions/  — doctor issues a prescription
    """
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsValidatedDoctor()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PrescriptionCreateSerializer
        return PrescriptionSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_patient:
            return Prescription.objects.filter(patient=user).select_related('doctor')
        elif user.is_doctor:
            return Prescription.objects.filter(doctor=user).select_related('patient')
        return Prescription.objects.none()

    def perform_create(self, serializer):
        serializer.save(doctor=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            PrescriptionSerializer(serializer.instance).data,
            status=status.HTTP_201_CREATED
        )


@extend_schema(tags=_TAG, summary='Detalhe de Receita')
class PrescriptionDetailView(generics.RetrieveAPIView):
    """
    GET /api/consultations/prescriptions/{id}/
    """
    serializer_class = PrescriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_patient:
            return Prescription.objects.filter(patient=user)
        elif user.is_doctor:
            return Prescription.objects.filter(doctor=user)
        return Prescription.objects.none()


# ─────────────────────────────────────────────
# Exam Requests
# ─────────────────────────────────────────────

@extend_schema_view(
    get=extend_schema(tags=_TAG, summary='Listar Solicitações de Exames'),
    post=extend_schema(tags=_TAG, summary='[Médico] Solicitar Exame', description='Solicita um exame para uma paciente vinculada. Requer CRM validado.'),
)
class ExamRequestListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/consultations/exam-requests/  — patient: own; doctor: issued
    POST /api/consultations/exam-requests/  — doctor issues an exam request
    """
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsValidatedDoctor()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ExamRequestCreateSerializer
        return ExamRequestSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_patient:
            return ExamRequest.objects.filter(patient=user).select_related('doctor')
        elif user.is_doctor:
            return ExamRequest.objects.filter(doctor=user).select_related('patient')
        return ExamRequest.objects.none()

    def perform_create(self, serializer):
        serializer.save(doctor=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            ExamRequestSerializer(serializer.instance).data,
            status=status.HTTP_201_CREATED
        )


@extend_schema(tags=_TAG, summary='Detalhe de Solicitação de Exame')
class ExamRequestDetailView(generics.RetrieveAPIView):
    """
    GET /api/consultations/exam-requests/{id}/
    """
    serializer_class = ExamRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_patient:
            return ExamRequest.objects.filter(patient=user)
        elif user.is_doctor:
            return ExamRequest.objects.filter(doctor=user)
        return ExamRequest.objects.none()
