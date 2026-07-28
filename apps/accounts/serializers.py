"""
Serializers for accounts app.
"""
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import PatientProfile, DoctorProfile

User = get_user_model()


class DoctorSummarySerializer(serializers.ModelSerializer):
    """Compact, read-only doctor representation nested inside a patient's profile."""
    user = serializers.SerializerMethodField()

    class Meta:
        model = DoctorProfile
        fields = ['id', 'user', 'crm', 'crm_state', 'specialty', 'institution']

    def get_user(self, obj):
        return {'id': obj.user.id, 'name': obj.user.name, 'email': obj.user.email}


class PatientProfileSerializer(serializers.ModelSerializer):
    doctor = DoctorSummarySerializer(read_only=True)

    class Meta:
        model = PatientProfile
        fields = [
            'id', 'cpf', 'gestational_age_weeks', 'expected_delivery_date',
            'last_menstrual_period', 'blood_type', 'height_cm',
            'pre_gestational_weight_kg', 'risk_conditions',
            'medical_history', 'family_medical_history',
            'doctor', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'gestational_age_weeks', 'created_at', 'updated_at']


class DoctorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorProfile
        fields = [
            'id', 'crm', 'crm_state', 'specialty', 'is_crm_validated',
            'institution', 'bio', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'is_crm_validated', 'validation_date', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    patient_profile = PatientProfileSerializer(read_only=True)
    doctor_profile = DoctorProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'name', 'user_type', 'phone',
            'date_of_birth', 'avatar', 'is_active',
            'date_joined', 'patient_profile', 'doctor_profile',
        ]
        read_only_fields = ['id', 'email', 'user_type', 'is_active', 'date_joined']


class PatientRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    # Patient profile fields
    cpf = serializers.CharField(required=False, max_length=14, allow_blank=True)
    gestational_age_weeks = serializers.IntegerField(required=False, allow_null=True)
    expected_delivery_date = serializers.DateField(required=False, allow_null=True)
    last_menstrual_period = serializers.DateField(required=False, allow_null=True)
    blood_type = serializers.CharField(max_length=5, required=False, allow_blank=True)
    height_cm = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    pre_gestational_weight_kg = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            'email', 'name', 'password', 'password_confirm',
            'phone', 'date_of_birth',
            'cpf', 'gestational_age_weeks', 'expected_delivery_date',
            'last_menstrual_period', 'blood_type', 'height_cm',
            'pre_gestational_weight_kg',
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({'password': 'As senhas não coincidem.'})
        cpf = attrs.get('cpf')
        if cpf and PatientProfile.objects.filter(cpf=cpf).exists():
            raise serializers.ValidationError({'cpf': 'Este CPF já está cadastrado.'})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        profile_fields = {
            k: validated_data.pop(k, None)
            for k in [
                'cpf', 'gestational_age_weeks', 'expected_delivery_date',
                'last_menstrual_period', 'blood_type', 'height_cm',
                'pre_gestational_weight_kg',
            ]
        }
        user = User.objects.create_user(
            user_type=User.UserType.PATIENT,
            **validated_data
        )
        # Normalize a blank/omitted CPF to NULL so multiple patients without
        # CPF don't collide on the unique constraint (empty string is not NULL).
        profile_fields['cpf'] = profile_fields.get('cpf') or None
        PatientProfile.objects.create(
            user=user,
            **{k: v for k, v in profile_fields.items() if v is not None or k == 'cpf'}
        )
        return user


class DoctorRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    # Doctor profile fields
    crm = serializers.CharField(max_length=20)
    crm_state = serializers.CharField(max_length=2)
    specialty = serializers.ChoiceField(choices=DoctorProfile.Specialty.choices)
    institution = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'email', 'name', 'password', 'password_confirm',
            'phone', 'date_of_birth',
            'crm', 'crm_state', 'specialty', 'institution',
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({'password': 'As senhas não coincidem.'})
        if DoctorProfile.objects.filter(crm=attrs.get('crm')).exists():
            raise serializers.ValidationError({'crm': 'Este CRM já está cadastrado.'})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        profile_fields = {
            k: validated_data.pop(k)
            for k in ['crm', 'crm_state', 'specialty']
        }
        profile_fields['institution'] = validated_data.pop('institution', '')

        user = User.objects.create_user(
            user_type=User.UserType.DOCTOR,
            **validated_data
        )
        DoctorProfile.objects.create(user=user, **profile_fields)
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['user_type'] = user.user_type
        token['name'] = user.name
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'name': self.user.name,
            'user_type': self.user.user_type,
        }
        return data


class AdminDoctorPatientSerializer(serializers.ModelSerializer):
    """Minimal patient info nested inside the admin doctor view."""
    id = serializers.IntegerField(source='user.id', read_only=True)
    name = serializers.CharField(source='user.name', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = PatientProfile
        fields = ['id', 'name', 'email', 'gestational_age_weeks']


class AdminDoctorSerializer(serializers.ModelSerializer):
    """[Admin] Full doctor overview: identity, CRM validation status, and linked patients."""
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    name = serializers.CharField(source='user.name', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)
    date_joined = serializers.DateTimeField(source='user.date_joined', read_only=True)
    specialty_display = serializers.CharField(source='get_specialty_display', read_only=True)
    patients = AdminDoctorPatientSerializer(many=True, read_only=True)
    patients_count = serializers.SerializerMethodField()

    class Meta:
        model = DoctorProfile
        fields = [
            'id', 'user_id', 'name', 'email', 'phone', 'date_joined',
            'crm', 'crm_state', 'specialty', 'specialty_display',
            'institution', 'bio',
            'is_crm_validated', 'validation_date', 'validation_notes',
            'patients', 'patients_count',
        ]

    def get_patients_count(self, obj):
        return obj.patients.count()


class AdminValidateDoctorSerializer(serializers.ModelSerializer):
    """[Admin] Updates CRM validation status for a doctor."""
    class Meta:
        model = DoctorProfile
        fields = ['is_crm_validated', 'validation_notes']

    def update(self, instance, validated_data):
        instance.is_crm_validated = validated_data.get('is_crm_validated', instance.is_crm_validated)
        instance.validation_notes = validated_data.get('validation_notes', instance.validation_notes)
        instance.validation_date = timezone.now()
        instance.save(update_fields=['is_crm_validated', 'validation_notes', 'validation_date'])
        return instance


class AdminPatientDoctorSerializer(serializers.ModelSerializer):
    """Minimal doctor info nested inside the admin patient view."""
    name = serializers.CharField(source='user.name', read_only=True)

    class Meta:
        model = DoctorProfile
        fields = ['id', 'name', 'crm', 'crm_state', 'is_crm_validated']


class AdminPatientSerializer(serializers.ModelSerializer):
    """[Admin] Full patient overview: identity, gestational data, and linked doctor."""
    id = serializers.IntegerField(source='user.id', read_only=True)
    name = serializers.CharField(source='user.name', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)
    date_joined = serializers.DateTimeField(source='user.date_joined', read_only=True)
    doctor = AdminPatientDoctorSerializer(read_only=True)

    class Meta:
        model = PatientProfile
        fields = [
            'id', 'name', 'email', 'phone', 'date_joined',
            'cpf', 'gestational_age_weeks', 'expected_delivery_date',
            'doctor',
        ]


class AdminLinkPatientSerializer(serializers.ModelSerializer):
    """[Admin] Creates/removes the relationship between a patient and a doctor."""
    doctor = serializers.PrimaryKeyRelatedField(
        queryset=DoctorProfile.objects.all(), allow_null=True
    )

    class Meta:
        model = PatientProfile
        fields = ['doctor']

    def validate_doctor(self, value):
        if value is not None and not value.is_crm_validated:
            raise serializers.ValidationError(
                'Não é possível vincular a um médico com CRM ainda não validado.'
            )
        return value


class UpdateProfileSerializer(serializers.ModelSerializer):
    patient_profile = PatientProfileSerializer(required=False)
    doctor_profile = DoctorProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ['name', 'phone', 'date_of_birth', 'avatar', 'patient_profile', 'doctor_profile']

    def update(self, instance, validated_data):
        patient_data = validated_data.pop('patient_profile', None)
        doctor_data = validated_data.pop('doctor_profile', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if patient_data and instance.is_patient:
            profile = instance.patient_profile
            for attr, value in patient_data.items():
                setattr(profile, attr, value)
            profile.save()
            profile.update_gestational_age()

        if doctor_data and instance.is_doctor:
            profile = instance.doctor_profile
            # Doctors cannot change CRM via this endpoint
            doctor_data.pop('crm', None)
            doctor_data.pop('is_crm_validated', None)
            for attr, value in doctor_data.items():
                setattr(profile, attr, value)
            profile.save()

        return instance
