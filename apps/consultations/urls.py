from django.urls import path
from .views import (
    ConsultationListCreateView,
    ConsultationDetailView,
    CancelConsultationView,
    PrescriptionListCreateView,
    PrescriptionDetailView,
    ExamRequestListCreateView,
    ExamRequestDetailView,
)

urlpatterns = [
    # Consultations
    path('', ConsultationListCreateView.as_view(), name='consultations-list'),
    path('<int:pk>/', ConsultationDetailView.as_view(), name='consultation-detail'),
    path('<int:pk>/cancel/', CancelConsultationView.as_view(), name='consultation-cancel'),

    # Prescriptions
    path('prescriptions/', PrescriptionListCreateView.as_view(), name='prescriptions-list'),
    path('prescriptions/<int:pk>/', PrescriptionDetailView.as_view(), name='prescription-detail'),

    # Exam Requests
    path('exam-requests/', ExamRequestListCreateView.as_view(), name='exam-requests-list'),
    path('exam-requests/<int:pk>/', ExamRequestDetailView.as_view(), name='exam-request-detail'),
]
