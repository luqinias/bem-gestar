"""
Risk score calculation service for BemGestar.
Uses a rule-based scoring system based on clinical thresholds.
"""
from decimal import Decimal
from apps.monitoring import clinical_rules as cr



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


def _linked_doctor_user(patient):
    """Returns the User of the patient's linked doctor, or None."""
    try:
        doctor_profile = patient.patient_profile.doctor
        return doctor_profile.user if doctor_profile else None
    except Exception:
        return None


def _create_notification_pair(
    patient, notification_type, severity,
    patient_title, patient_message, doctor_title, doctor_message,
    **related
):
    """
    Creates one Notification row for the patient (patient-voiced copy) and,
    if she has a linked doctor, a second row for that doctor (doctor-voiced
    copy) — each is its own DB record scoped to its recipient, instead of a
    single row shared/read by both.
    """
    from apps.monitoring.models import Notification

    created = [Notification.objects.create(
        recipient=patient,
        patient=patient,
        notification_type=notification_type,
        severity=severity,
        title=patient_title,
        message=patient_message,
        **related,
    )]

    doctor_user = _linked_doctor_user(patient)
    if doctor_user:
        created.append(Notification.objects.create(
            recipient=doctor_user,
            patient=patient,
            notification_type=notification_type,
            severity=severity,
            title=doctor_title,
            message=doctor_message,
            **related,
        ))

    return created


def check_and_create_alerts(vital_sign=None, symptom=None, patient=None, risk_score_obj=None):
    """
    Analyze new data and create notifications when clinical thresholds are
    exceeded — one row per recipient (patient and, if linked, her doctor).
    """
    from apps.monitoring.models import Notification
    notifications_created = []
    t = THRESHOLDS

    if vital_sign:
        sys_bp = vital_sign.systolic_bp
        dia_bp = vital_sign.diastolic_bp
        name = vital_sign.patient.name

        # Severe hypertension alert
        if sys_bp and sys_bp >= t['systolic_bp_very_high']:
            notifications_created += _create_notification_pair(
                vital_sign.patient, Notification.NotificationType.HYPERTENSION, Notification.Severity.URGENT,
                'Hipertensão Grave Detectada',
                f'Pressão arterial sistólica de {sys_bp} mmHg detectada. Procure atendimento médico imediatamente.',
                f'Hipertensão Grave — {name}',
                f'{name} registrou pressão arterial sistólica de {sys_bp} mmHg (hipertensão grave).',
                vital_sign=vital_sign,
            )

        elif sys_bp and sys_bp >= t['systolic_bp_high']:
            notifications_created += _create_notification_pair(
                vital_sign.patient, Notification.NotificationType.HYPERTENSION, Notification.Severity.WARNING,
                'Pressão Arterial Elevada',
                f'Pressão arterial sistólica de {sys_bp} mmHg. Monitore e informe seu médico.',
                f'Pressão Arterial Elevada — {name}',
                f'{name} registrou pressão arterial sistólica de {sys_bp} mmHg.',
                vital_sign=vital_sign,
            )

        # Hypotension alert
        if sys_bp and sys_bp <= t['systolic_bp_low']:
            notifications_created += _create_notification_pair(
                vital_sign.patient, Notification.NotificationType.HYPOTENSION, Notification.Severity.WARNING,
                'Pressão Arterial Baixa',
                f'Pressão arterial sistólica de {sys_bp} mmHg. Hidrate-se e descanse.',
                f'Pressão Arterial Baixa — {name}',
                f'{name} registrou pressão arterial sistólica de {sys_bp} mmHg (hipotensão).',
                vital_sign=vital_sign,
            )

        # Low oxygen saturation
        if vital_sign.oxygen_saturation and vital_sign.oxygen_saturation <= t['oxygen_very_low']:
            notifications_created += _create_notification_pair(
                vital_sign.patient, Notification.NotificationType.LOW_OXYGEN, Notification.Severity.URGENT,
                'Saturação de Oxigênio Crítica',
                f'Saturação de {vital_sign.oxygen_saturation}%. Procure atendimento médico urgente.',
                f'Saturação de Oxigênio Crítica — {name}',
                f'{name} registrou saturação de oxigênio de {vital_sign.oxygen_saturation}%.',
                vital_sign=vital_sign,
            )

        # Fever
        if vital_sign.temperature_celsius:
            temp = float(vital_sign.temperature_celsius)
            if temp >= t['temperature_high']:
                severity = Notification.Severity.URGENT if temp >= t['temperature_very_high'] else Notification.Severity.WARNING
                notifications_created += _create_notification_pair(
                    vital_sign.patient, Notification.NotificationType.FEVER, severity,
                    'Febre Detectada',
                    f'Temperatura de {temp}°C. Informe seu médico.',
                    f'Febre Detectada — {name}',
                    f'{name} registrou temperatura de {temp}°C.',
                    vital_sign=vital_sign,
                )

    if symptom:
        # Severe symptoms always trigger alerts
        if symptom.severity == 'severe' or symptom.symptom_type in HIGH_RISK_SYMPTOMS:
            name = symptom.patient.name
            notifications_created += _create_notification_pair(
                symptom.patient, Notification.NotificationType.SEVERE_SYMPTOM,
                Notification.Severity.URGENT if symptom.severity == 'severe' else Notification.Severity.WARNING,
                f'Sintoma Importante: {symptom.get_symptom_type_display()}',
                (
                    f'Você registrou {symptom.get_symptom_type_display()} '
                    f'com intensidade {symptom.get_severity_display()}. Informe seu médico.'
                ),
                f'Sintoma Importante: {symptom.get_symptom_type_display()} — {name}',
                (
                    f'{name} registrou {symptom.get_symptom_type_display()} '
                    f'com intensidade {symptom.get_severity_display()}.'
                ),
                symptom=symptom,
            )

    if risk_score_obj and risk_score_obj.risk_level in ['high', 'critical']:
        severity = Notification.Severity.URGENT if risk_score_obj.risk_level == 'critical' else Notification.Severity.WARNING
        name = risk_score_obj.patient.name
        notifications_created += _create_notification_pair(
            risk_score_obj.patient, Notification.NotificationType.HIGH_RISK_SCORE, severity,
            f'Score de Risco {risk_score_obj.get_risk_level_display()}',
            (
                f'Seu score de risco gestacional está em {risk_score_obj.score} '
                f'({risk_score_obj.get_risk_level_display()}). Entre em contato com seu médico.'
            ),
            f'Score de Risco {risk_score_obj.get_risk_level_display()} — {name}',
            (
                f'O score de risco gestacional de {name} está em {risk_score_obj.score} '
                f'({risk_score_obj.get_risk_level_display()}).'
            ),
            risk_score=risk_score_obj,
        )

    return notifications_created


def run_clinical_rules(vital_sign=None, symptom=None, patient=None):
    """
    Executa o motor de regras clínicas e persiste os alertas gerados.

    Para cada alerta identificado:
      1. Cria um ClinicalAlert (entidade principal).
      2. Cria uma Notification referenciando o ClinicalAlert (sem duplicar dados).

    Retorna a lista de ClinicalAlert criados.
    """
    from apps.monitoring.models import ClinicalAlert, Notification

    if patient is None:
        return []

    alerts_data = cr.evaluate_rules(
        patient=patient,
        vital_sign=vital_sign,
        symptom=symptom,
    )

    # Map severity to Notification.Severity
    severity_map = {
        ClinicalAlert.Severity.LOW: Notification.Severity.INFO,
        ClinicalAlert.Severity.MEDIUM: Notification.Severity.WARNING,
        ClinicalAlert.Severity.HIGH: Notification.Severity.URGENT,
    }

    created_alerts = []
    for data in alerts_data:
        related_vs = data.pop('related_vital_sign_obj', None)

        alert = ClinicalAlert.objects.create(
            patient=patient,
            condition_name=data['condition_name'],
            severity=data['severity'],
            reason=data['reason'],
            guidance=data['guidance'],
            symptoms_used=data['symptoms_used'],
            vital_signs_used=data['vital_signs_used'],
            related_vital_sign=related_vs,
            related_symptom=symptom,
            status=ClinicalAlert.Status.ACTIVE,
            viewed=False,
        )
        created_alerts.append(alert)

        # Gera Notification para o paciente (referenciando o alerta)
        notif_severity = severity_map.get(data['severity'], Notification.Severity.WARNING)
        _create_clinical_notification(patient, alert, notif_severity)

    return created_alerts


def _create_clinical_notification(patient, clinical_alert, notif_severity):
    """
    Cria uma notificação para a paciente e, se vinculada, para o médico.
    A notificação referencia o ClinicalAlert e não duplica o conteúdo.
    """
    from apps.monitoring.models import Notification

    severity_label = {
        'low': 'ℹ️',
        'medium': '⚠️',
        'high': '🚨',
    }.get(clinical_alert.severity, '⚠️')

    title = f'{severity_label} {clinical_alert.condition_name}'
    message = clinical_alert.reason

    Notification.objects.create(
        recipient=patient,
        patient=patient,
        notification_type=Notification.NotificationType.GENERAL,
        severity=notif_severity,
        title=title,
        message=message,
        clinical_alert=clinical_alert,
    )

    doctor_user = _linked_doctor_user(patient)
    if doctor_user:
        name = patient.name
        Notification.objects.create(
            recipient=doctor_user,
            patient=patient,
            notification_type=Notification.NotificationType.GENERAL,
            severity=notif_severity,
            title=f'{severity_label} {clinical_alert.condition_name} — {name}',
            message=f'{name}: {clinical_alert.reason}',
            clinical_alert=clinical_alert,
        )
