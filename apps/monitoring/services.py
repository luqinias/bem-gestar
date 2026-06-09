"""
Risk score calculation service for BemGestar.
Uses a rule-based scoring system based on clinical thresholds.
"""
from decimal import Decimal


# Clinical thresholds for alert generation
THRESHOLDS = {
    # Blood pressure (systolic/diastolic)
    'systolic_bp_high': 140,       # Hypertension
    'systolic_bp_very_high': 160,  # Severe hypertension
    'systolic_bp_low': 90,         # Hypotension
    'diastolic_bp_high': 90,       # Hypertension
    'diastolic_bp_very_high': 110, # Severe hypertension
    'diastolic_bp_low': 60,        # Hypotension

    # Heart rate
    'heart_rate_high': 100,        # Tachycardia
    'heart_rate_very_high': 120,   # Severe tachycardia
    'heart_rate_low': 50,          # Bradycardia

    # Temperature
    'temperature_high': 37.8,      # Fever
    'temperature_very_high': 38.5, # High fever

    # Oxygen saturation
    'oxygen_low': 95,              # Low saturation
    'oxygen_very_low': 90,         # Critical

    # Blood glucose
    'glucose_high': 140,           # High (fasting reference)
    'glucose_very_high': 200,      # Critical
}

# Symptom weights for risk scoring
SYMPTOM_SEVERITY_WEIGHTS = {
    'mild': 2,
    'moderate': 5,
    'severe': 15,
}

HIGH_RISK_SYMPTOMS = {
    'bleeding': 20,
    'blurred_vision': 15,
    'chest_pain': 20,
    'reduced_fetal_movement': 20,
    'severe_headache': 15,
    'contractions': 10,
}


def calculate_risk_score(vital_sign=None, symptom=None, patient=None):
    """
    Calculate a risk score (0-100) based on vital signs and symptoms.
    Returns a dict with score, risk_level, and contributing_factors.
    """
    score = Decimal('0')
    factors = {}

    if vital_sign:
        vs_score, vs_factors = _score_vital_signs(vital_sign)
        score += vs_score
        factors.update(vs_factors)

    if symptom:
        sym_score, sym_factors = _score_symptom(symptom)
        score += sym_score
        factors.update(sym_factors)

    # Cap score at 100
    score = min(score, Decimal('100'))

    risk_level = _determine_risk_level(score)

    return {
        'score': score,
        'risk_level': risk_level,
        'contributing_factors': factors,
    }


def _score_vital_signs(vital_sign):
    """Calculate score contribution from vital signs."""
    score = Decimal('0')
    factors = {}
    t = THRESHOLDS

    # Blood pressure scoring
    sys_bp = vital_sign.systolic_bp
    dia_bp = vital_sign.diastolic_bp

    if sys_bp:
        if sys_bp >= t['systolic_bp_very_high']:
            score += 30
            factors['systolic_bp'] = {'value': sys_bp, 'status': 'critical', 'points': 30}
        elif sys_bp >= t['systolic_bp_high']:
            score += 15
            factors['systolic_bp'] = {'value': sys_bp, 'status': 'elevated', 'points': 15}
        elif sys_bp <= t['systolic_bp_low']:
            score += 10
            factors['systolic_bp'] = {'value': sys_bp, 'status': 'low', 'points': 10}

    if dia_bp:
        if dia_bp >= t['diastolic_bp_very_high']:
            score += 25
            factors['diastolic_bp'] = {'value': dia_bp, 'status': 'critical', 'points': 25}
        elif dia_bp >= t['diastolic_bp_high']:
            score += 12
            factors['diastolic_bp'] = {'value': dia_bp, 'status': 'elevated', 'points': 12}

    # Heart rate
    hr = vital_sign.heart_rate
    if hr:
        if hr >= t['heart_rate_very_high']:
            score += 20
            factors['heart_rate'] = {'value': hr, 'status': 'critical', 'points': 20}
        elif hr >= t['heart_rate_high']:
            score += 8
            factors['heart_rate'] = {'value': hr, 'status': 'elevated', 'points': 8}
        elif hr <= t['heart_rate_low']:
            score += 5
            factors['heart_rate'] = {'value': hr, 'status': 'low', 'points': 5}

    # Temperature
    temp = vital_sign.temperature_celsius
    if temp:
        temp_float = float(temp)
        if temp_float >= t['temperature_very_high']:
            score += 20
            factors['temperature'] = {'value': temp_float, 'status': 'high_fever', 'points': 20}
        elif temp_float >= t['temperature_high']:
            score += 10
            factors['temperature'] = {'value': temp_float, 'status': 'fever', 'points': 10}

    # Oxygen saturation
    spo2 = vital_sign.oxygen_saturation
    if spo2:
        if spo2 <= t['oxygen_very_low']:
            score += 30
            factors['oxygen_saturation'] = {'value': spo2, 'status': 'critical', 'points': 30}
        elif spo2 <= t['oxygen_low']:
            score += 15
            factors['oxygen_saturation'] = {'value': spo2, 'status': 'low', 'points': 15}

    # Blood glucose
    glucose = vital_sign.blood_glucose
    if glucose:
        glucose_float = float(glucose)
        if glucose_float >= t['glucose_very_high']:
            score += 20
            factors['blood_glucose'] = {'value': glucose_float, 'status': 'critical', 'points': 20}
        elif glucose_float >= t['glucose_high']:
            score += 8
            factors['blood_glucose'] = {'value': glucose_float, 'status': 'elevated', 'points': 8}

    return score, factors


def _score_symptom(symptom):
    """Calculate score contribution from a symptom."""
    score = Decimal('0')
    factors = {}

    # Base severity weight
    severity_weight = SYMPTOM_SEVERITY_WEIGHTS.get(symptom.severity, 2)

    # Extra weight for high-risk symptoms
    extra_weight = HIGH_RISK_SYMPTOMS.get(symptom.symptom_type, 0)

    total = severity_weight + extra_weight
    score += total

    factors[f'symptom_{symptom.symptom_type}'] = {
        'type': symptom.symptom_type,
        'severity': symptom.severity,
        'points': total,
    }

    return score, factors


def _determine_risk_level(score):
    """Map score to risk level."""
    from apps.monitoring.models import RiskScore
    score_float = float(score)
    if score_float >= 80:
        return RiskScore.RiskLevel.CRITICAL
    elif score_float >= 60:
        return RiskScore.RiskLevel.HIGH
    elif score_float >= 30:
        return RiskScore.RiskLevel.MEDIUM
    return RiskScore.RiskLevel.LOW


def check_and_create_alerts(vital_sign=None, symptom=None, patient=None, risk_score_obj=None):
    """
    Analyze new data and create alerts when clinical thresholds are exceeded.
    """
    from apps.monitoring.models import Alert
    alerts_created = []
    t = THRESHOLDS

    if vital_sign:
        sys_bp = vital_sign.systolic_bp
        dia_bp = vital_sign.diastolic_bp

        # Severe hypertension alert
        if sys_bp and sys_bp >= t['systolic_bp_very_high']:
            alert = Alert.objects.create(
                patient=vital_sign.patient,
                alert_type=Alert.AlertType.HYPERTENSION,
                severity=Alert.Severity.URGENT,
                title='Hipertensão Grave Detectada',
                message=(
                    f'Pressão arterial sistólica de {sys_bp} mmHg detectada. '
                    'Procure atendimento médico imediatamente.'
                ),
                vital_sign=vital_sign,
            )
            alerts_created.append(alert)

        elif sys_bp and sys_bp >= t['systolic_bp_high']:
            alert = Alert.objects.create(
                patient=vital_sign.patient,
                alert_type=Alert.AlertType.HYPERTENSION,
                severity=Alert.Severity.WARNING,
                title='Pressão Arterial Elevada',
                message=f'Pressão arterial sistólica de {sys_bp} mmHg. Monitore e informe seu médico.',
                vital_sign=vital_sign,
            )
            alerts_created.append(alert)

        # Hypotension alert
        if sys_bp and sys_bp <= t['systolic_bp_low']:
            alert = Alert.objects.create(
                patient=vital_sign.patient,
                alert_type=Alert.AlertType.HYPOTENSION,
                severity=Alert.Severity.WARNING,
                title='Pressão Arterial Baixa',
                message=f'Pressão arterial sistólica de {sys_bp} mmHg. Hidrate-se e descanse.',
                vital_sign=vital_sign,
            )
            alerts_created.append(alert)

        # Low oxygen saturation
        if vital_sign.oxygen_saturation and vital_sign.oxygen_saturation <= t['oxygen_very_low']:
            alert = Alert.objects.create(
                patient=vital_sign.patient,
                alert_type=Alert.AlertType.LOW_OXYGEN,
                severity=Alert.Severity.URGENT,
                title='Saturação de Oxigênio Crítica',
                message=(
                    f'Saturação de {vital_sign.oxygen_saturation}%. '
                    'Procure atendimento médico urgente.'
                ),
                vital_sign=vital_sign,
            )
            alerts_created.append(alert)

        # Fever
        if vital_sign.temperature_celsius:
            temp = float(vital_sign.temperature_celsius)
            if temp >= t['temperature_high']:
                severity = Alert.Severity.URGENT if temp >= t['temperature_very_high'] else Alert.Severity.WARNING
                alert = Alert.objects.create(
                    patient=vital_sign.patient,
                    alert_type=Alert.AlertType.FEVER,
                    severity=severity,
                    title='Febre Detectada',
                    message=f'Temperatura de {temp}°C. Informe seu médico.',
                    vital_sign=vital_sign,
                )
                alerts_created.append(alert)

    if symptom:
        # Severe symptoms always trigger alerts
        if symptom.severity == 'severe' or symptom.symptom_type in HIGH_RISK_SYMPTOMS:
            alert = Alert.objects.create(
                patient=symptom.patient,
                alert_type=Alert.AlertType.SEVERE_SYMPTOM,
                severity=Alert.Severity.URGENT if symptom.severity == 'severe' else Alert.Severity.WARNING,
                title=f'Sintoma Importante: {symptom.get_symptom_type_display()}',
                message=(
                    f'Você registrou {symptom.get_symptom_type_display()} '
                    f'com intensidade {symptom.get_severity_display()}. '
                    'Informe seu médico.'
                ),
                symptom=symptom,
            )
            alerts_created.append(alert)

    if risk_score_obj and risk_score_obj.risk_level in ['high', 'critical']:
        severity = Alert.Severity.URGENT if risk_score_obj.risk_level == 'critical' else Alert.Severity.WARNING
        alert = Alert.objects.create(
            patient=risk_score_obj.patient,
            alert_type=Alert.AlertType.HIGH_RISK_SCORE,
            severity=severity,
            title=f'Score de Risco {risk_score_obj.get_risk_level_display()}',
            message=(
                f'Seu score de risco gestacional está em {risk_score_obj.score} '
                f'({risk_score_obj.get_risk_level_display()}). '
                'Entre em contato com seu médico.'
            ),
            risk_score=risk_score_obj,
        )
        alerts_created.append(alert)

    return alerts_created
