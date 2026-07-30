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
    PrescriptionSerializer, PrescriptionCreateSerializer, PrescriptionUpdateSerializer,
    ExamRequestSerializer, ExamRequestCreateSerializer, ExamRequestUpdateSerializer,
)

_TAG = ['consultations']


from apps.monitoring.services import create_consultation_notification, create_exam_notification


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
    filterset_fields = ['status', 'consultation_type', 'patient']

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

    def filter_queryset(self, queryset):
        # Apply standard filters first
        queryset = super().filter_queryset(queryset)
        
        # Translate frontend scheduled_at to backend scheduled_date
        ordering = self.request.query_params.get('ordering')
        if ordering:
            params = [p.strip() for p in ordering.split(',')]
            order_by_args = []
            for p in params:
                if p == 'scheduled_at':
                    order_by_args.append('scheduled_date')
                elif p == '-scheduled_at':
                    order_by_args.append('-scheduled_date')
                elif hasattr(queryset.model, p.replace('-', '')):
                    order_by_args.append(p)
            if order_by_args:
                queryset = queryset.order_by(*order_by_args)
        return queryset

    def perform_create(self, serializer):
        consultation = serializer.save(doctor=self.request.user)
        # Disparar notificação para a paciente
        dt_str = consultation.scheduled_date.strftime("%d/%m/%Y às %H:%M")
        create_consultation_notification(
            patient=consultation.patient,
            doctor=consultation.doctor,
            notification_type='appointment_scheduled',
            severity='info',
            patient_title='📅 Consulta Agendada',
            patient_message=f'Consulta agendada para {dt_str} com Dr(a). {consultation.doctor.name}.'
        )

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
    delete=extend_schema(tags=_TAG, summary='[Médico] Excluir Consulta', description='Remove definitivamente um agendamento (ex.: cadastro incorreto). Para desmarcar uma consulta válida, prefira cancelar.'),
)
class ConsultationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/consultations/{id}/  — get consultation detail
    PATCH  /api/consultations/{id}/  — doctor updates notes/type/date
    DELETE /api/consultations/{id}/  — doctor deletes the consultation record
    """
    serializer_class = ConsultationSerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsValidatedDoctor()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return Consultation.objects.filter(doctor=user) if user.is_doctor else Consultation.objects.none()
        if user.is_patient:
            return Consultation.objects.filter(patient=user)
        elif user.is_doctor:
            return Consultation.objects.filter(doctor=user)
        return Consultation.objects.none()

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        consultation = self.get_object()
        dt_str = consultation.scheduled_date.strftime("%d/%m/%Y às %H:%M")
        create_consultation_notification(
            patient=consultation.patient,
            doctor=consultation.doctor,
            notification_type='appointment_updated',
            severity='info',
            patient_title='✏️ Consulta Alterada',
            patient_message=f'Sua consulta com Dr(a). {consultation.doctor.name} foi alterada para {dt_str}.'
        )
        return response


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

        dt_str = consultation.scheduled_date.strftime("%d/%m/%Y às %H:%M")
        if user.is_patient:
            create_consultation_notification(
                patient=consultation.patient,
                doctor=consultation.doctor,
                notification_type='appointment_cancelled',
                severity='warning',
                doctor_title=f'❌ Consulta Cancelada — {consultation.patient.name}',
                doctor_message=f'A paciente {consultation.patient.name} cancelou a consulta de {dt_str}.'
            )
        else:
            create_consultation_notification(
                patient=consultation.patient,
                doctor=consultation.doctor,
                notification_type='appointment_cancelled',
                severity='warning',
                patient_title='❌ Consulta Cancelada',
                patient_message=f'Sua consulta agendada para {dt_str} foi cancelada pelo médico.'
            )

        return Response(ConsultationSerializer(consultation).data)


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
    filterset_fields = ['patient', 'prescription_type']

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


@extend_schema_view(
    get=extend_schema(tags=_TAG, summary='Detalhe de Receita'),
    patch=extend_schema(tags=_TAG, summary='[Médico] Editar Receita'),
    delete=extend_schema(tags=_TAG, summary='[Médico] Excluir Receita'),
)
class PrescriptionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/consultations/prescriptions/{id}/  — retrieve
    PATCH  /api/consultations/prescriptions/{id}/  — doctor edits their own prescription
    DELETE /api/consultations/prescriptions/{id}/  — doctor deletes their own prescription
    """
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return PrescriptionUpdateSerializer
        return PrescriptionSerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsValidatedDoctor()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return Prescription.objects.filter(doctor=user) if user.is_doctor else Prescription.objects.none()
        if user.is_patient:
            return Prescription.objects.filter(patient=user)
        elif user.is_doctor:
            return Prescription.objects.filter(doctor=user)
        return Prescription.objects.none()

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        return Response(PrescriptionSerializer(self.get_object()).data)


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
    filterset_fields = ['patient', 'status', 'priority']

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
        exam_req = serializer.save(doctor=self.request.user)
        create_exam_notification(
            patient=exam_req.patient,
            doctor=exam_req.doctor,
            notification_type='exam_requested',
            severity='info',
            title='🧪 Novo Exame Solicitado',
            message=f'O Dr(a). {exam_req.doctor.name} solicitou o exame: {exam_req.exam_name}.'
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            ExamRequestSerializer(serializer.instance).data,
            status=status.HTTP_201_CREATED
        )


@extend_schema_view(
    get=extend_schema(tags=_TAG, summary='Detalhe de Solicitação de Exame'),
    patch=extend_schema(tags=_TAG, summary='[Médico] Editar/Cancelar Exame', description='Edita dados do exame ou muda o status (ex.: cancelar, marcar como realizado com resultado).'),
    delete=extend_schema(tags=_TAG, summary='[Médico] Excluir Solicitação de Exame'),
)
class ExamRequestDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/consultations/exam-requests/{id}/  — retrieve
    PATCH  /api/consultations/exam-requests/{id}/  — doctor edits or changes status (e.g. cancel)
    DELETE /api/consultations/exam-requests/{id}/  — doctor deletes their own exam request
    """
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ExamRequestUpdateSerializer
        return ExamRequestSerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsValidatedDoctor()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return ExamRequest.objects.filter(doctor=user) if user.is_doctor else ExamRequest.objects.none()
        if user.is_patient:
            return ExamRequest.objects.filter(patient=user)
        elif user.is_doctor:
            return ExamRequest.objects.filter(doctor=user)
        return ExamRequest.objects.none()

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        exam_req = self.get_object()
        if exam_req.result_notes or exam_req.status == ExamRequest.Status.COMPLETED:
            create_exam_notification(
                patient=exam_req.patient,
                doctor=exam_req.doctor,
                notification_type='exam_result',
                severity='info',
                title='📋 Resultado de Exame Disponível',
                message=f'O resultado do seu exame "{exam_req.exam_name}" foi disponibilizado.'
            )
        return response

