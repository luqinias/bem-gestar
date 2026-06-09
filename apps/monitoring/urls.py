"""
URL patterns for monitoring app.
"""
from django.urls import path
from .views import (
    VitalSignListCreateView,
    VitalSignDetailView,
    SymptomListCreateView,
    RiskScoreListView,
    LatestRiskScoreView,
    AlertListView,
    MarkAlertReadView,
    ClinicalDashboardView,
    PatientTimelineView,
)

urlpatterns = [
    # Vital Signs
    path('vital-signs/', VitalSignListCreateView.as_view(), name='vital-signs-list'),
    path('vital-signs/<int:pk>/', VitalSignDetailView.as_view(), name='vital-sign-detail'),

    # Symptoms
    path('symptoms/', SymptomListCreateView.as_view(), name='symptoms-list'),

    # Risk Score
    path('risk-score/', RiskScoreListView.as_view(), name='risk-score-list'),
    path('risk-score/latest/', LatestRiskScoreView.as_view(), name='risk-score-latest'),

    # Alerts
    path('alerts/', AlertListView.as_view(), name='alerts-list'),
    path('alerts/<int:pk>/read/', MarkAlertReadView.as_view(), name='alert-read'),

    # Dashboard (Doctor)
    path('dashboard/', ClinicalDashboardView.as_view(), name='clinical-dashboard'),
    path('timeline/', PatientTimelineView.as_view(), name='patient-timeline'),
]
