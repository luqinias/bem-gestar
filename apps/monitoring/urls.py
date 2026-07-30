"""
URL patterns for monitoring app.
"""
from django.urls import path
from .views import (
    VitalSignListCreateView,
    VitalSignDetailView,
    SymptomListCreateView,
    SymptomDetailView,
    RiskScoreListView,
    LatestRiskScoreView,
    NotificationListView,
    MarkNotificationReadView,
    ClinicalDashboardView,
    PatientTimelineView,
    ClinicalAlertListView,
    ClinicalAlertDetailView,
    MarkAlertViewedView,
    DoctorRecentAlertsView,
)

urlpatterns = [
    # Vital Signs
    path('vital-signs/', VitalSignListCreateView.as_view(), name='vital-signs-list'),
    path('vital-signs/<int:pk>/', VitalSignDetailView.as_view(), name='vital-sign-detail'),

    # Symptoms
    path('symptoms/', SymptomListCreateView.as_view(), name='symptoms-list'),
    path('symptoms/<int:pk>/', SymptomDetailView.as_view(), name='symptom-detail'),

    # Risk Score
    path('risk-score/', RiskScoreListView.as_view(), name='risk-score-list'),
    path('risk-score/latest/', LatestRiskScoreView.as_view(), name='risk-score-latest'),

    # Notifications
    path('notifications/', NotificationListView.as_view(), name='notifications-list'),
    path('notifications/<int:pk>/read/', MarkNotificationReadView.as_view(), name='notification-read'),

    # Clinical Alerts
    path('alerts/', ClinicalAlertListView.as_view(), name='clinical-alerts-list'),
    path('alerts/recent/', DoctorRecentAlertsView.as_view(), name='clinical-alerts-recent'),
    path('alerts/<int:pk>/', ClinicalAlertDetailView.as_view(), name='clinical-alert-detail'),
    path('alerts/<int:pk>/viewed/', MarkAlertViewedView.as_view(), name='clinical-alert-viewed'),

    # Dashboard (Doctor)
    path('dashboard/', ClinicalDashboardView.as_view(), name='clinical-dashboard'),
    path('timeline/', PatientTimelineView.as_view(), name='patient-timeline'),
]
