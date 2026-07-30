"""
Custom User model and profiles for BemGestar.
Supports two main roles: PATIENT and DOCTOR.
"""
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('O email é obrigatório.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', User.UserType.ADMIN)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class UserType(models.TextChoices):
        PATIENT = 'patient', 'Paciente'
        DOCTOR = 'doctor', 'Médico'
        ADMIN = 'admin', 'Administrador'

    email = models.EmailField(unique=True, verbose_name='Email')
    name = models.CharField(max_length=255, verbose_name='Nome completo')
    user_type = models.CharField(
        max_length=10,
        choices=UserType.choices,
        default=UserType.PATIENT,
        verbose_name='Tipo de usuário'
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name='Telefone')
    date_of_birth = models.DateField(null=True, blank=True, verbose_name='Data de nascimento')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name='Foto de perfil')

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = UserManager()

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def __str__(self):
        return f'{self.name} ({self.get_user_type_display()})'

    @property
    def is_patient(self):
        return self.user_type == self.UserType.PATIENT

    @property
    def is_doctor(self):
        return self.user_type == self.UserType.DOCTOR

    @property
    def is_admin(self):
        return self.user_type == self.UserType.ADMIN


class PatientProfile(models.Model):
    """
    Extended profile for patients (gestantes).
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')

    # Personal data
    cpf = models.CharField(max_length=14, blank=True, null=True, unique=True, verbose_name='CPF')

    # Gestational data
    gestational_age_weeks = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name='Semana gestacional atual'
    )
    expected_delivery_date = models.DateField(null=True, blank=True, verbose_name='Data prevista do parto')
    last_menstrual_period = models.DateField(null=True, blank=True, verbose_name='DUM (Data da última menstruação)')

    # Health data
    blood_type = models.CharField(max_length=5, blank=True, verbose_name='Tipo sanguíneo')
    height_cm = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Altura (cm)'
    )
    pre_gestational_weight_kg = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Peso pré-gestacional (kg)'
    )
    risk_conditions = models.TextField(
        blank=True, verbose_name='Condições de risco pré-existentes'
    )

    # Medical history
    medical_history = models.TextField(
        blank=True, verbose_name='Histórico médico (doenças anteriores)'
    )
    family_medical_history = models.TextField(
        blank=True, verbose_name='Histórico de doenças na família'
    )

    # Linked doctor
    doctor = models.ForeignKey(
        'DoctorProfile',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='patients',
        verbose_name='Médico responsável'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Perfil da Paciente'
        verbose_name_plural = 'Perfis das Pacientes'

    def __str__(self):
        return f'Paciente: {self.user.name}'

    def calculate_expected_delivery_date(self):
        """
        Calculates expected delivery date:
        1. Naegele rule: LMP + 280 days (40 weeks)
        2. Fallback: Current Date + (40 - gestational_age_weeks) weeks
        """
        from datetime import date, timedelta
        if self.last_menstrual_period:
            return self.last_menstrual_period + timedelta(days=280)
        elif self.gestational_age_weeks is not None:
            remaining_weeks = max(0, 40 - self.gestational_age_weeks)
            return date.today() + timedelta(weeks=remaining_weeks)
        return None

    def save(self, *args, **kwargs):
        # Auto-calculate expected delivery date if not explicitly set or if data changed
        computed_edd = self.calculate_expected_delivery_date()
        if computed_edd:
            self.expected_delivery_date = computed_edd
        super().save(*args, **kwargs)

    def update_gestational_age(self):
        """Recalculate gestational age based on LMP and re-evaluate EDD."""
        if self.last_menstrual_period:
            from datetime import date
            delta = date.today() - self.last_menstrual_period
            self.gestational_age_weeks = delta.days // 7
            computed_edd = self.calculate_expected_delivery_date()
            if computed_edd:
                self.expected_delivery_date = computed_edd
            self.save(update_fields=['gestational_age_weeks', 'expected_delivery_date'])


class DoctorProfile(models.Model):

    """
    Extended profile for doctors (médicos).
    Requires CRM validation before accessing clinical features.
    """
    class Specialty(models.TextChoices):
        OBSTETRICS = 'obstetrics', 'Obstetrícia'
        GYNECOLOGY = 'gynecology', 'Ginecologia'
        MATERNAL_FETAL = 'maternal_fetal', 'Medicina Materno-Fetal'
        GENERAL = 'general', 'Clínica Geral'
        OTHER = 'other', 'Outra'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')

    crm = models.CharField(max_length=20, unique=True, verbose_name='CRM')
    crm_state = models.CharField(max_length=2, verbose_name='Estado do CRM')
    specialty = models.CharField(
        max_length=30, choices=Specialty.choices,
        default=Specialty.OBSTETRICS, verbose_name='Especialidade'
    )

    # Validation status
    is_crm_validated = models.BooleanField(default=False, verbose_name='CRM validado')
    validation_date = models.DateTimeField(null=True, blank=True, verbose_name='Data da validação')
    validation_notes = models.TextField(blank=True, verbose_name='Observações da validação')

    # Professional info
    institution = models.CharField(max_length=255, blank=True, verbose_name='Instituição')
    bio = models.TextField(blank=True, verbose_name='Biografia profissional')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Perfil do Médico'
        verbose_name_plural = 'Perfis dos Médicos'

    def __str__(self):
        return f'Dr(a). {self.user.name} — CRM {self.crm}/{self.crm_state}'

    @property
    def can_access_clinical(self):
        """Doctor can only access clinical features after CRM validation."""
        return self.is_crm_validated
