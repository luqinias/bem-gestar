from typing import Optional
from django.db.models import QuerySet
from django.contrib.auth import get_user_model
from .models import ARModel, ARTelemetry

User = get_user_model()

def get_ar_model_by_week(week: int) -> Optional[ARModel]:
    """
    Selects a specific ARModel by week.
    """
    return ARModel.objects.filter(week=week).first()


def get_user_telemetries(user: User) -> QuerySet[ARTelemetry]:
    """
    Selects all telemetry records for a given user.
    """
    return ARTelemetry.objects.filter(user=user)
