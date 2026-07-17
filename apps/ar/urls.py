from django.urls import path
from .views import ARBabyModelView, ARTelemetryView

app_name = 'ar'

urlpatterns = [
    path('baby/', ARBabyModelView.as_view(), name='baby-model'),
    path('telemetry/', ARTelemetryView.as_view(), name='telemetry'),
]
