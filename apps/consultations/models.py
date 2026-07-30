"""
Models for consultations app: appointments, prescriptions, and exam requests.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone


class Consultation(models.Model):
    """
    Consultas agendadas pelo médico, visíveis e canceláveis pela paciente.
    """
    objects = models.Manager()
    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Agendada'
        COMPLETED = 'completed', 'Realizada'
        CANCELLED = 'cancelled', 'Cancelada'
        NO_SHOW = 'no_show', 'Paciente não compareceu'

    class ConsultationType(models.TextChoices):
        IN_PERSON = 'in_person', 'Presencial'
        TELECONSULTATION = 'teleconsultation', 'Teleconsulta'

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='consultations_as_patient',
        limit_choices_to={'user_type': 'patient'},
        verbose_name='Paciente',
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='consultations_as_doctor',
        limit_choices_to={'user_type': 'doctor'},
        verbose_name='Médico',
    )

    scheduled_date = models.DateTimeField(verbose_name='Data e hora agendada')
    consultation_type = models.CharField(
        max_length=20, choices=ConsultationType.choices,
        default=ConsultationType.IN_PERSON, verbose_name='Tipo de consulta'
    )
    location = models.CharField(
        max_length=500, blank=True, verbose_name='Local/Link da consulta'
    )
    status = models.CharField(
        max_length=15, choices=Status.choices,
        default=Status.SCHEDULED, verbose_name='Status'
    )
    notes = models.TextField(blank=True, verbose_name='Anotações')
    cancellation_reason = models.TextField(blank=True, verbose_name='Motivo do cancelamento')
    cancelled_at = models.DateTimeField(null=True, blank=True, verbose_name='Cancelado em')
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='cancelled_consultations',
        verbose_name='Cancelado por',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Consulta'
        verbose_name_plural = 'Consultas'
        ordering = ['-scheduled_date']

    def __str__(self):
        dt_str = getattr(self.scheduled_date, 'strftime', lambda f: str)( "%d/%m/%Y %H:%M" )
        return f'Consulta: {self.patient.name} com Dr(a). {self.doctor.name} — {dt_str}'

    def cancel(self, cancelled_by, reason=''):
        self.status = str(self.Status.CANCELLED)  # type: ignore
        self.cancelled_by = cancelled_by
        self.cancellation_reason = str(reason)  # type: ignore
        self.cancelled_at = timezone.now()  # type: ignore
        self.save(update_fields=['status', 'cancelled_by', 'cancellation_reason', 'cancelled_at'])


class Prescription(models.Model):
    """
    Receitas digitais emitidas pelo médico, acessíveis pela paciente.
    """
    objects = models.Manager()
    class PrescriptionType(models.TextChoices):
        MEDICATION = 'medication', 'Medicação'
        EXAM = 'exam', 'Exame'
        REFERRAL = 'referral', 'Encaminhamento'

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='prescriptions_received',
        limit_choices_to={'user_type': 'patient'},
        verbose_name='Paciente',
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='prescriptions_issued',
        limit_choices_to={'user_type': 'doctor'},
        verbose_name='Médico',
    )
    consultation = models.ForeignKey(
        Consultation,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='prescriptions',
        verbose_name='Consulta relacionada',
    )

    prescription_type = models.CharField(
        max_length=15, choices=PrescriptionType.choices,
        default=PrescriptionType.MEDICATION, verbose_name='Tipo'
    )
    title = models.CharField(max_length=200, verbose_name='Título')
    content = models.TextField(verbose_name='Conteúdo da receita')
    instructions = models.TextField(blank=True, verbose_name='Instruções de uso')
    valid_until = models.DateField(null=True, blank=True, verbose_name='Válida até')
    digital_signature = models.CharField(
        max_length=500, blank=True, verbose_name='Assinatura digital'
    )

    issued_at = models.DateTimeField(default=timezone.now, verbose_name='Emitida em')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Receita Digital'
        verbose_name_plural = 'Receitas Digitais'
        ordering = ['-issued_at']

    def __str__(self):
        return f'Receita: {self.title} — {self.patient.name}'


class ExamRequest(models.Model):
    """
    Solicitações de exames pelo médico, visíveis pela paciente.
    """
    objects = models.Manager()
    class Priority(models.TextChoices):
        ROUTINE = 'routine', 'Rotina'
        URGENT = 'urgent', 'Urgente'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendente'
        COMPLETED = 'completed', 'Realizado'
        CANCELLED = 'cancelled', 'Cancelado'

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='exam_requests_received',
        limit_choices_to={'user_type': 'patient'},
        verbose_name='Paciente',
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='exam_requests_issued',
        limit_choices_to={'user_type': 'doctor'},
        verbose_name='Médico',
    )
    consultation = models.ForeignKey(
        Consultation,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='exam_requests',
        verbose_name='Consulta relacionada',
    )

    exam_name = models.CharField(max_length=200, verbose_name='Nome do exame')
    clinical_indication = models.TextField(verbose_name='Indicação clínica')
    priority = models.CharField(
        max_length=10, choices=Priority.choices,
        default=Priority.ROUTINE, verbose_name='Prioridade'
    )
    status = models.CharField(
        max_length=15, choices=Status.choices,
        default=Status.PENDING, verbose_name='Status'
    )
    notes = models.TextField(blank=True, verbose_name='Observações')
    result_notes = models.TextField(blank=True, verbose_name='Resultado (anotações)')

    requested_at = models.DateTimeField(default=timezone.now, verbose_name='Solicitado em')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Solicitação de Exame'
        verbose_name_plural = 'Solicitações de Exames'
        ordering = ['-requested_at']

    def __str__(self):
        return f'Exame: {self.exam_name} — {self.patient.name}'
