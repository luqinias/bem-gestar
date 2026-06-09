"""
Custom permission classes for BemGestar.
"""
from rest_framework.permissions import BasePermission


class IsPatient(BasePermission):
    """Allows access only to authenticated patients."""
    message = 'Acesso restrito a pacientes.'

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_patient
        )


class IsDoctor(BasePermission):
    """Allows access only to authenticated doctors."""
    message = 'Acesso restrito a médicos.'

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_doctor
        )


class IsValidatedDoctor(BasePermission):
    """Allows access only to doctors with validated CRM."""
    message = 'Acesso restrito a médicos com CRM validado.'

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated and request.user.is_doctor):
            return False
        try:
            return request.user.doctor_profile.is_crm_validated
        except Exception:
            return False


class IsPatientOrValidatedDoctor(BasePermission):
    """Allows access to patients and validated doctors."""
    message = 'Acesso restrito a pacientes ou médicos validados.'

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_patient:
            return True
        if request.user.is_doctor:
            try:
                return request.user.doctor_profile.is_crm_validated
            except Exception:
                return False
        return False


class IsOwnerOrDoctor(BasePermission):
    """
    Object-level permission: allow patients to access own data,
    or the linked doctor to access patient data.
    """
    def has_object_permission(self, request, view, obj):
        # Get the patient user from the object
        patient_user = getattr(obj, 'patient', None) or getattr(obj, 'user', None)
        if patient_user == request.user:
            return True
        # Check if requesting user is the linked doctor
        if request.user.is_doctor:
            try:
                doctor_profile = request.user.doctor_profile
                if hasattr(patient_user, 'patient_profile'):
                    return patient_user.patient_profile.doctor == doctor_profile
            except Exception:
                pass
        return False
