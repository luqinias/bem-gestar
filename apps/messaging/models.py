"""
Models for messaging app — async communication between patient and doctor.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone


class Conversation(models.Model):
    """
    A conversation thread between a patient and a doctor.
    Only one conversation per patient-doctor pair.
    """
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations_as_patient',
        limit_choices_to={'user_type': 'patient'},
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations_as_doctor',
        limit_choices_to={'user_type': 'doctor'},
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Conversa'
        verbose_name_plural = 'Conversas'
        ordering = ['-updated_at']
        unique_together = [['patient', 'doctor']]

    def __str__(self):
        return f'Conversa: {self.patient.name} ↔ {self.doctor.name}'

    @property
    def last_message(self):
        return self.messages.order_by('-sent_at').first()

    def unread_count(self, user):
        return self.messages.filter(read=False).exclude(sender=user).count()


class Message(models.Model):
    """
    A single message in a conversation.
    Supports offline queuing via 'pending' status.
    """
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendente (offline)'
        SENT = 'sent', 'Enviada'
        READ = 'read', 'Lida'

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
    )

    content = models.TextField(verbose_name='Conteúdo')
    status = models.CharField(
        max_length=10, choices=Status.choices,
        default=Status.SENT, verbose_name='Status',
    )
    read = models.BooleanField(default=False, verbose_name='Lida')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='Lida em')

    # Attachment support (future)
    attachment = models.FileField(
        upload_to='message_attachments/',
        null=True, blank=True,
        verbose_name='Anexo',
    )

    sent_at = models.DateTimeField(default=timezone.now, verbose_name='Enviada em')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Mensagem'
        verbose_name_plural = 'Mensagens'
        ordering = ['sent_at']

    def __str__(self):
        return f'Msg de {self.sender.name}: {self.content[:50]}'

    def mark_as_read(self):
        if not self.read:
            self.read = True
            self.read_at = timezone.now()
            self.status = self.Status.READ
            self.save(update_fields=['read', 'read_at', 'status'])
