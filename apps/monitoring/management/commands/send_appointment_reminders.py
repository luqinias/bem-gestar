"""
Management command to send appointment reminders 24h before scheduled date.
Usage: python manage.py send_appointment_reminders
"""
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.consultations.models import Consultation
from apps.monitoring.services import create_consultation_notification


class Command(BaseCommand):
    help = 'Envia lembretes automáticos para consultas agendadas nas próximas 24 horas.'

    def handle(self, *args, **options):
        now = timezone.now()
        next_24h = now + timedelta(hours=24)

        consultations = Consultation.objects.filter(
            status=Consultation.Status.SCHEDULED,
            scheduled_date__gte=now,
            scheduled_date__lte=next_24h,
        ).select_related('patient', 'doctor')

        created_count = 0
        for consultation in consultations:
            time_str = consultation.scheduled_date.strftime("%H:%M")

            notifs = create_consultation_notification(
                patient=consultation.patient,
                doctor=consultation.doctor,
                notification_type='appointment_reminder',
                severity='info',
                patient_title='Lembrete de Consulta',
                patient_message=f'Você possui uma consulta agendada amanhã às {time_str} com Dr(a). {consultation.doctor.name}.',
                doctor_title=f'Lembrete de Atendimento — {consultation.patient.name}',
                doctor_message=f'Você possui atendimento agendado amanhã às {time_str} com a paciente {consultation.patient.name}.'
            )

            created_count += len(notifs)

        self.stdout.write(
            self.style.SUCCESS(f'Sucesso: {created_count} lembretes de consulta processados/criados.')
        )
