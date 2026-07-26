import logging
from decimal import Decimal
from typing import Optional, Dict
from django.contrib.auth import get_user_model
from .models import ARModel, ARTelemetry

logger = logging.getLogger(__name__)
User = get_user_model()

# Hadlock prenatal growth curve reference table
# week -> (height_cm, weight_grams)
GROWTH_CURVE: Dict[int, tuple[float, int]] = {
    8: (1.6, 1),
    9: (2.3, 2),
    10: (3.1, 4),
    11: (4.1, 7),
    12: (5.4, 14),
    13: (7.4, 23),
    14: (8.7, 43),
    15: (10.1, 70),
    16: (11.6, 100),
    17: (13.0, 140),
    18: (14.2, 190),
    19: (15.3, 240),
    20: (25.6, 300),
    21: (26.7, 360),
    22: (27.8, 430),
    23: (28.9, 501),
    24: (30.0, 600),
    25: (34.6, 660),
    26: (35.6, 760),
    27: (36.6, 875),
    28: (37.6, 1005),
    29: (38.6, 1153),
    30: (39.9, 1319),
    31: (41.1, 1502),
    32: (42.4, 1702),
    33: (43.7, 1918),
    34: (45.0, 2146),
    35: (46.2, 2383),
    36: (47.4, 2622),
    37: (48.6, 2859),
    38: (49.8, 3083),
    39: (50.7, 3288),
    40: (51.2, 3462),
    41: (51.7, 3597),
    42: (51.5, 3685)
}



def get_growth_estimate(week: int) -> tuple[float, int]:
    """
    Returns estimated fetal height (cm) and weight (grams) using the standard growth curve.
    """
    if week in GROWTH_CURVE:
        return GROWTH_CURVE[week]
    if week < 8:
        return GROWTH_CURVE[8]
    return GROWTH_CURVE[42]


def get_spatial_dimensions_estimate(week: int) -> dict:
    """
    Computes spatial dimensions estimates (in meters) for a given week.
    Returns length, width, depth, and bounding box coordinates.
    """
    height_cm, _ = get_growth_estimate(week)
    length_m = height_cm / 100.0
    width_m = length_m * 0.45
    depth_m = length_m * 0.40
    return {
        'real_length_meters': Decimal(str(round(length_m, 3))),
        'real_width_meters': Decimal(str(round(width_m, 3))),
        'real_depth_meters': Decimal(str(round(depth_m, 3))),
        'bounding_box_x': Decimal(str(round(width_m, 3))),
        'bounding_box_y': Decimal(str(round(length_m, 3))),
        'bounding_box_z': Decimal(str(round(depth_m, 3))),
    }


def find_closest_ar_model(week: int) -> Optional[ARModel]:
    """
    Selects the closest ARModel available in the database for the given gestational week.
    """
    # Check exact match first
    model = ARModel.objects.filter(week=week).first()
    if model:
        return model

    # Fallback: get the closest model week
    models = ARModel.objects.all()
    if not models.exists():
        return None

    closest_model = min(models, key=lambda m: abs(m.week - week))
    return closest_model


def create_ar_telemetry(
    user: User,
    time_in_experience_seconds: int,
    views_count: int,
    captures_count: int,
    model_used: str,
    gestational_week: int,
    avg_fps: Decimal,
    errors_logged: str,
    crashes_count: int
) -> ARTelemetry:
    """
    Creates and registers a new AR experience telemetry log.
    """
    telemetry = ARTelemetry.objects.create(
        user=user,
        time_in_experience_seconds=time_in_experience_seconds,
        views_count=views_count,
        captures_count=captures_count,
        model_used=model_used,
        gestational_week=gestational_week,
        avg_fps=avg_fps,
        errors_logged=errors_logged,
        crashes_count=crashes_count
    )
    return telemetry
