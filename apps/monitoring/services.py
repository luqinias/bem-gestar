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


def check_and_create_alerts(vital_sign=None, symptom=None, patient=None, risk_score_obj=None):
    """
    Desativado: Notificações de limiares vitais isolados foram removidas.
    Apenas alertas clínicos derivados do motor de regras (run_clinical_rules) geram notificações.
    """
    return []


def run_clinical_rules(vital_sign=None, symptom=None, patient=None):
    """
    Executa o motor de regras clínicas e persiste os alertas gerados.
    """
    from apps.monitoring.models import ClinicalAlert, Notification

    if patient is None:
        return []

    alerts_data = cr.evaluate_rules(
        patient=patient,
        vital_sign=vital_sign,
        symptom=symptom,
    )

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

        notif_severity = severity_map.get(data['severity'], Notification.Severity.WARNING)
        _create_clinical_notification(patient, alert, notif_severity)

    return created_alerts


def _create_clinical_notification(patient, clinical_alert, notif_severity):
    """
    Cria uma notificação para a paciente e, se vinculada, para o médico.
    A notificação referencia o ClinicalAlert e usa o tipo CLINICAL_ALERT.
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
        notification_type=Notification.NotificationType.CLINICAL_ALERT,
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
            notification_type=Notification.NotificationType.CLINICAL_ALERT,
            severity=notif_severity,
            title=f'{severity_label} {clinical_alert.condition_name} — {name}',
            message=f'{name}: {clinical_alert.reason}',
            clinical_alert=clinical_alert,
        )


def create_consultation_notification(
    patient, doctor, notification_type, severity, patient_title=None, patient_message=None, doctor_title=None, doctor_message=None
):
    """
    Cria notificação para paciente e/ou médico referente a consultas.
    """
    from apps.monitoring.models import Notification

    created = []
    if patient_title and patient_message and patient:
        created.append(Notification.objects.create(
            recipient=patient,
            patient=patient,
            notification_type=notification_type,
            severity=severity,
            title=patient_title,
            message=patient_message,
        ))

    if doctor_title and doctor_message and doctor:
        created.append(Notification.objects.create(
            recipient=doctor,
            patient=patient,
            notification_type=notification_type,
            severity=severity,
            title=doctor_title,
            message=doctor_message,
        ))
    return created


def create_exam_notification(patient, doctor, notification_type, severity, title, message):
    """
    Cria notificação referente a solicitação ou resultado de exames.
    """
    from apps.monitoring.models import Notification

    return Notification.objects.create(
        recipient=patient,
        patient=patient,
        notification_type=notification_type,
        severity=severity,
        title=title,
        message=message,
    )


def create_chat_notification(sender, recipient, message_text):
    """
    Cria notificação de nova mensagem do chat para o destinatário.
    """
    from apps.monitoring.models import Notification

    patient = sender if sender.is_patient else (recipient if recipient.is_patient else sender)

    if sender.is_doctor:
        title = f'💬 Nova Mensagem de Dr(a). {sender.name.split()[0]}'
        msg = f'Dr(a). {sender.name}: {message_text[:80]}'
    else:
        title = f'💬 Nova Mensagem de {sender.name.split()[0]}'
        msg = f'{sender.name}: {message_text[:80]}'

    return Notification.objects.create(
        recipient=recipient,
        patient=patient,
        notification_type=Notification.NotificationType.CHAT_MESSAGE,
        severity=Notification.Severity.INFO,
        title=title,
        message=msg,
    )


def reevaluate_patient_health_status(patient, deleted_vs_id=None, deleted_symptom_id=None):
    """
    Recalculates risk score and resolves obsolete alerts after vital sign or symptom deletion.
    """
    from apps.monitoring.models import VitalSign, Symptom, RiskScore, ClinicalAlert

    latest_vs = VitalSign.objects.filter(patient=patient).order_by('-recorded_at').first()
    latest_sym = Symptom.objects.filter(patient=patient).order_by('-recorded_at').first()

    if latest_vs or latest_sym:
        result = calculate_risk_score(vital_sign=latest_vs, symptom=latest_sym, patient=patient)
        RiskScore.objects.create(
            patient=patient,
            score=result['score'],
            risk_level=result['risk_level'],
            contributing_factors=result['contributing_factors'],
        )
    else:
        RiskScore.objects.create(
            patient=patient,
            score=0,
            risk_level='low',
            contributing_factors={},
        )

    active_alerts = ClinicalAlert.objects.filter(patient=patient, status=ClinicalAlert.Status.ACTIVE)
    for alert in active_alerts:
        if alert.related_vital_sign_id is None and alert.related_symptom_id is None:
            alert.status = ClinicalAlert.Status.RESOLVED
            alert.save()
        elif deleted_vs_id and alert.related_vital_sign_id == deleted_vs_id:
            alert.status = ClinicalAlert.Status.RESOLVED
            alert.save()
        elif deleted_symptom_id and alert.related_symptom_id == deleted_symptom_id:
            alert.status = ClinicalAlert.Status.RESOLVED
            alert.save()
