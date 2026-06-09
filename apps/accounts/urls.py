"""
URL patterns for accounts app.
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    PatientRegisterView,
    DoctorRegisterView,
    CustomTokenObtainPairView,
    MeView,
    LogoutView,
    PatientsListView,
    PatientDetailView,
    LinkDoctorView,
)

urlpatterns = [
    # Authentication
    path('register/patient/', PatientRegisterView.as_view(), name='patient-register'),
    path('register/doctor/', DoctorRegisterView.as_view(), name='doctor-register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Profile
    path('me/', MeView.as_view(), name='me'),
    path('me/link-doctor/', LinkDoctorView.as_view(), name='link-doctor'),

    # Doctor-only patient management
    path('patients/', PatientsListView.as_view(), name='patients-list'),
    path('patients/<int:pk>/', PatientDetailView.as_view(), name='patient-detail'),
]
