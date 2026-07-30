from django.contrib import admin
from .models import ClinicalAlert, VitalSign, Symptom, RiskScore, Notification


@admin.register(ClinicalAlert)
class ClinicalAlertAdmin(admin.ModelAdmin):
    list_display = ['condition_name', 'severity', 'patient', 'status', 'viewed', 'created_at']
    list_filter = ['severity', 'status', 'viewed']
    search_fields = ['condition_name', 'patient__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
