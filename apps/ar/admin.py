from django.contrib import admin
from .models import ARModel, ARTelemetry

@admin.register(ARModel)
class ARModelAdmin(admin.ModelAdmin):
    list_display = ('week', 'estimated_height_cm', 'estimated_weight_grams', 'animation', 'scale', 'updated_at')
    list_filter = ('week', 'animation')
    search_fields = ('week', 'animation')
    ordering = ('week',)


@admin.register(ARTelemetry)
class ARTelemetryAdmin(admin.ModelAdmin):
    list_display = ('user', 'gestational_week', 'time_in_experience_seconds', 'captures_count', 'avg_fps', 'crashes_count', 'created_at')
    list_filter = ('gestational_week', 'avg_fps', 'crashes_count', 'created_at')
    search_fields = ('user__email', 'model_used')
    readonly_fields = ('user', 'time_in_experience_seconds', 'views_count', 'captures_count', 'model_used', 'gestational_week', 'avg_fps', 'errors_logged', 'crashes_count', 'created_at')
    ordering = ('-created_at',)
