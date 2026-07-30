"""
Models for gestational monitoring: vital signs, symptoms, risk scores and alerts.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone


class ClinicalAlert(models.Model):
    """
    Alerta clínico gestacional gerado automaticamente pelo motor de regras.
    É a entidade principal do sistema de alertas.
    As Notification apenas referenciam este modelo para evitar duplicação.
    """

    class Severity(models.TextChoices):
        LOW = 'low', 'Informativo'
        MEDIUM = 'medium', 'Atenção'
        HIGH = 'high', 'Urgente'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Ativo'
        RESOLVED = 'resolved', 'Resolvido'

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='clinical_alerts',
        limit_choices_to={'user_type': 'patient'},
        verbose_name='Paciente',
    )

    # Identificação da condição clínica
    condition_name = models.CharField(
        max_length=120, verbose_name='Condição identificada'
    )
    severity = models.CharField(
        max_length=10, choices=Severity.choices,
        default=Severity.MEDIUM, verbose_name='Severidade'
    )

    # Conteúdo exibido para a usuária
    reason = models.TextField(verbose_name='Motivo do alerta')
    guidance = models.TextField(verbose_name='Orientações')

    # Dados clínicos utilizados na regra
    symptoms_used = models.JSONField(
        default=list, verbose_name='Sintomas utilizados'
    )
    vital_signs_used = models.JSONField(
        default=dict, verbose_name='Sinais vitais utilizados'
    )

    # Registros relacionados (opcionais)
    related_vital_sign = models.ForeignKey(
        'VitalSign', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='clinical_alerts',
        verbose_name='Sinal vital relacionado',
    )
    related_symptom = models.ForeignKey(
        'Symptom', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='clinical_alerts',
        verbose_name='Sintoma relacionado',
    )

    # Estado do alerta
    status = models.CharField(
        max_length=10, choices=Status.choices,
        default=Status.ACTIVE, verbose_name='Status'
    )
    viewed = models.BooleanField(default=False, verbose_name='Visualizado')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Alerta Clínico'
        verbose_name_plural = 'Alertas Clínicos'
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.get_severity_display()}] {self.condition_name} — {self.patient.name}'


class VitalSign(models.Model):
    """
    Registro de sinais vitais pela paciente.
    """
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vital_signs',
        limit_choices_to={'user_type': 'patient'},
    )

    # Measurements
    systolic_bp = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name='Pressão sistólica (mmHg)'
    )
    diastolic_bp = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name='Pressão diastólica (mmHg)'
    )
    heart_rate = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name='Frequência cardíaca (bpm)'
    )
    temperature_celsius = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True,
        verbose_name='Temperatura (°C)'
    )
    weight_kg = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Peso (kg)'
    )
    oxygen_saturation = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name='Saturação de oxigênio (%)'
    )
    blood_glucose = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True,
        verbose_name='Glicemia (mg/dL)'
    )
    sleep_hours = models.DecimalField(
        max_digits=3, decimal_places=1, null=True, blank=True,
        verbose_name='Horas de sono'
    )

    notes = models.TextField(blank=True, verbose_name='Observações')
    recorded_at = models.DateTimeField(default=timezone.now, verbose_name='Registrado em')
    created_at = models.DateTimeField(auto_now_add=True)

    # Offline support
    synced = models.BooleanField(default=True, verbose_name='Sincronizado')

    class Meta:
        verbose_name = 'Sinal Vital'
        verbose_name_plural = 'Sinais Vitais'
        ordering = ['-recorded_at']

    def __str__(self):
        return f'Sinais Vitais de {self.patient.name} em {self.recorded_at.strftime("%d/%m/%Y %H:%M")}'


class Symptom(models.Model):
    """
    Registro de sintomas gestacionais pela paciente.
    """
    class Severity(models.TextChoices):
        MILD = 'mild', 'Leve'
        MODERATE = 'moderate', 'Moderado'
        SEVERE = 'severe', 'Grave'

    SYMPTOM_CHOICES = [
        ('headache', 'Dor de cabeça'),
        ('nausea', 'Náusea'),
        ('vomiting', 'Vômito'),
        ('abdominal_pain', 'Dor abdominal'),
        ('bleeding', 'Sangramento'),
        ('swelling', 'Inchaço (edema)'),
        ('blurred_vision', 'Visão turva'),
        ('chest_pain', 'Dor no peito'),
        ('shortness_of_breath', 'Falta de ar'),
        ('reduced_fetal_movement', 'Redução dos movimentos fetais'),
        ('burning_urination', 'Ardência ao urinar'),
        ('fever', 'Febre'),
        ('dizziness', 'Tontura'),
        ('lower_back_pain', 'Dor lombar'),
        ('contractions', 'Contrações'),
        ('other', 'Outro'),
    ]

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='symptoms',
        limit_choices_to={'user_type': 'patient'},
    )

    symptom_type = models.CharField(
        max_length=30, choices=SYMPTOM_CHOICES, verbose_name='Tipo de sintoma'
    )
    severity = models.CharField(
        max_length=10, choices=Severity.choices,
        default=Severity.MILD, verbose_name='Intensidade'
    )
    description = models.TextField(blank=True, verbose_name='Descrição livre')
    duration_hours = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name='Duração aproximada (horas)'
    )

    recorded_at = models.DateTimeField(default=timezone.now, verbose_name='Registrado em')
    created_at = models.DateTimeField(auto_now_add=True)
    synced = models.BooleanField(default=True, verbose_name='Sincronizado')

    class Meta:
        verbose_name = 'Sintoma'
        verbose_name_plural = 'Sintomas'
        ordering = ['-recorded_at']

    def __str__(self):
        return f'{self.get_symptom_type_display()} ({self.get_severity_display()}) — {self.patient.name}'


class RiskScore(models.Model):
    """
    Score de risco gestacional calculado automaticamente pelo sistema.
    Não pode ser alterado pelo usuário.
    """
    class RiskLevel(models.TextChoices):
        LOW = 'low', 'Baixo'
        MEDIUM = 'medium', 'Médio'
        HIGH = 'high', 'Alto'
        CRITICAL = 'critical', 'Crítico'

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='risk_scores',
        limit_choices_to={'user_type': 'patient'},
    )

    score = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name='Score (0-100)'
    )
    risk_level = models.CharField(
        max_length=10, choices=RiskLevel.choices,
        default=RiskLevel.LOW, verbose_name='Nível de risco'
    )

    # Factors that contributed to this score
    contributing_factors = models.JSONField(
        default=dict, verbose_name='Fatores contribuintes'
    )

    calculated_at = models.DateTimeField(auto_now_add=True, verbose_name='Calculado em')

    class Meta:
        verbose_name = 'Score de Risco'
        verbose_name_plural = 'Scores de Risco'
        ordering = ['-calculated_at']
        get_latest_by = 'calculated_at'

    def __str__(self):
        return f'Score {self.score} ({self.get_risk_level_display()}) — {self.patient.name}'


class Notification(models.Model):
    """
    Per-recipient notification generated when risk patterns are identified.
    One row per recipient: a patient event (e.g. a severe symptom) creates a
    row for the patient AND a separate row for her linked doctor, each with
    its own copy and its own read status — no row is shared between users.
    """
    class NotificationType(models.TextChoices):
        HYPERTENSION = 'hypertension', 'Hipertensão'
        HYPOTENSION = 'hypotension', 'Hipotensão'
        TACHYCARDIA = 'tachycardia', 'Taquicardia'
        FEVER = 'fever', 'Febre'
        LOW_OXYGEN = 'low_oxygen', 'Saturação baixa'
        HIGH_GLUCOSE = 'high_glucose', 'Glicemia elevada'
        SEVERE_SYMPTOM = 'severe_symptom', 'Sintoma grave'
        HIGH_RISK_SCORE = 'high_risk_score', 'Score de risco elevado'
        REDUCED_FETAL_MOVEMENT = 'reduced_fetal_movement', 'Redução movimentos fetais'
        GENERAL = 'general', 'Geral'

    class Severity(models.TextChoices):
        INFO = 'info', 'Informativo'
        WARNING = 'warning', 'Atenção'
        URGENT = 'urgent', 'Urgente'

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Destinatário',
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_notifications',
        limit_choices_to={'user_type': 'patient'},
        verbose_name='Paciente relacionada',
    )

    notification_type = models.CharField(
        max_length=30, choices=NotificationType.choices, verbose_name='Tipo'
    )
    severity = models.CharField(
        max_length=10, choices=Severity.choices,
        default=Severity.WARNING, verbose_name='Severidade'
    )
    title = models.CharField(max_length=200, verbose_name='Título')
    message = models.TextField(verbose_name='Mensagem')

    # Related records
    vital_sign = models.ForeignKey(
        VitalSign, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='notifications', verbose_name='Sinal vital relacionado'
    )
    symptom = models.ForeignKey(
        Symptom, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='notifications', verbose_name='Sintoma relacionado'
    )
    risk_score = models.ForeignKey(
        RiskScore, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='notifications', verbose_name='Score relacionado'
    )

    read = models.BooleanField(default=False, verbose_name='Lida')

    # Referência ao alerta clínico (quando gerado pelo motor de regras)
    clinical_alert = models.ForeignKey(
        ClinicalAlert, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='notifications',
        verbose_name='Alerta clínico relacionado',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.get_severity_display()}] {self.title} → {self.recipient.name}'
