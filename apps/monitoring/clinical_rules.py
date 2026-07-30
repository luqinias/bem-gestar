"""
Motor de Regras Clínicas Gestacionais — BemGestar
==================================================
Cada regra é uma função que recebe contexto clínico e retorna None (não disparada)
ou um dict com os campos do alerta a ser criado.

Para adicionar uma nova regra no futuro:
  1. Defina uma função _rule_<nome>(ctx) seguindo o mesmo padrão.
  2. Adicione-a à lista CLINICAL_RULES ao final do arquivo.
  Nenhuma outra alteração é necessária.
"""

from datetime import timedelta
from django.utils import timezone


# ---------------------------------------------------------------------------
# Contexto passado para cada regra
# ctx = {
#   "patient":        User object,
#   "vital":          VitalSign (pode ser None),
#   "recent_vitals":  list[VitalSign] — últimas 24h,
#   "recent_symptoms": list[Symptom]  — últimas 24h,
#   "symptom":        Symptom (pode ser None),  # o registro atual
# }
# ---------------------------------------------------------------------------

def _has_symptom(symptom_list, *symptom_types):
    """Verifica se a lista contém pelo menos um dos tipos de sintoma informados."""
    present = {s.symptom_type for s in symptom_list}
    return bool(present.intersection(set(symptom_types)))


def _symptom_names(symptom_list, *symptom_types):
    """Retorna os display-names dos sintomas presentes que interessam à regra."""
    result = []
    for s in symptom_list:
        if s.symptom_type in symptom_types:
            result.append(s.get_symptom_type_display())
    seen = []
    for n in result:
        if n not in seen:
            seen.append(n)
    return seen


def _latest_vital_value(vital_list, field):
    """Retorna o valor mais recente de um campo de sinal vital."""
    for v in vital_list:
        val = getattr(v, field, None)
        if val is not None:
            return val
    return None


# ---------------------------------------------------------------------------
# Regras individuais
# ---------------------------------------------------------------------------

def _rule_preeclampsia(ctx):
    """Possível Pré-eclâmpsia — PA ≥ 140/90 + pelo menos um sintoma grave."""
    vitals = ctx['recent_vitals']
    symptoms = ctx['recent_symptoms']

    severe_symptoms = [
        'headache', 'blurred_vision', 'swelling',
        'abdominal_pain', 'nausea', 'vomiting',
    ]

    bp_elevated = any(
        (v.systolic_bp is not None and v.systolic_bp >= 140) or
        (v.diastolic_bp is not None and v.diastolic_bp >= 90)
        for v in vitals
    )
    if not bp_elevated:
        return None

    if not _has_symptom(symptoms, *severe_symptoms):
        return None

    vs = next(
        (v for v in vitals if (v.systolic_bp and v.systolic_bp >= 140) or (v.diastolic_bp and v.diastolic_bp >= 90)), None
    )
    used_symptoms = _symptom_names(symptoms, *severe_symptoms)
    return {
        'condition_name': 'Possível Pré-eclâmpsia',
        'severity': 'high',
        'reason': (
            'Seus registros podem indicar uma elevação da pressão arterial '
            'combinada a outros sintomas compatíveis com pré-eclâmpsia.'
        ),
        'guidance': (
            'Procure atendimento médico imediatamente. '
            'Este alerta é apenas uma ferramenta de apoio e não substitui avaliação médica.'
        ),
        'symptoms_used': used_symptoms,
        'vital_signs_used': {
            'Pressão sistólica': f'{vs.systolic_bp} mmHg' if vs else None,
            'Pressão diastólica': f'{vs.diastolic_bp} mmHg' if vs else None,
        },
        'related_vital_sign_obj': vs,
    }


def _rule_hypertension(ctx):
    """Hipertensão Gestacional — PA ≥ 140/90 sem sintomas graves."""
    vitals = ctx['recent_vitals']
    symptoms = ctx['recent_symptoms']

    severe_symptoms = [
        'headache', 'blurred_vision', 'swelling',
        'abdominal_pain', 'nausea', 'vomiting',
    ]

    bp_elevated = any(
        (v.systolic_bp is not None and v.systolic_bp >= 140) or
        (v.diastolic_bp is not None and v.diastolic_bp >= 90)
        for v in vitals
    )
    if not bp_elevated:
        return None

    # Se tiver sintomas graves -> pré-eclâmpsia cuida
    if _has_symptom(symptoms, *severe_symptoms):
        return None

    vs = next(
        (v for v in vitals if (v.systolic_bp and v.systolic_bp >= 140) or (v.diastolic_bp and v.diastolic_bp >= 90)), None
    )
    return {
        'condition_name': 'Hipertensão Gestacional',
        'severity': 'medium',
        'reason': (
            'Seus registros indicam pressão arterial acima de 140/90 mmHg, '
            'o que pode sugerir hipertensão gestacional.'
        ),
        'guidance': (
            'Recomenda-se entrar em contato com sua equipe de saúde nas próximas horas. '
            'Este alerta é apenas uma ferramenta de apoio e não substitui avaliação médica.'
        ),
        'symptoms_used': [],
        'vital_signs_used': {
            'Pressão sistólica': f'{vs.systolic_bp} mmHg' if vs else None,
            'Pressão diastólica': f'{vs.diastolic_bp} mmHg' if vs else None,
        },
        'related_vital_sign_obj': vs,
    }


def _rule_hypoglycemia(ctx):
    """Hipoglicemia — glicemia < 70 + tontura ou náusea."""
    vitals = ctx['recent_vitals']
    symptoms = ctx['recent_symptoms']

    low_glucose_vs = next(
        (v for v in vitals
         if v.blood_glucose is not None and float(v.blood_glucose) < 70),
        None
    )
    if not low_glucose_vs:
        return None

    if not _has_symptom(symptoms, 'dizziness', 'nausea'):
        return None

    return {
        'condition_name': 'Possível Hipoglicemia',
        'severity': 'medium',
        'reason': (
            'Seus registros podem indicar glicemia abaixo de 70 mg/dL '
            'combinada a sintomas como tontura ou náusea.'
        ),
        'guidance': (
            'Recomenda-se entrar em contato com sua equipe de saúde nas próximas horas. '
            'Este alerta é apenas uma ferramenta de apoio e não substitui avaliação médica.'
        ),
        'symptoms_used': _symptom_names(symptoms, 'dizziness', 'nausea'),
        'vital_signs_used': {
            'Glicemia': f'{float(low_glucose_vs.blood_glucose):.1f} mg/dL',
        },
        'related_vital_sign_obj': low_glucose_vs,
    }


def _rule_hyperglycemia(ctx):
    """Hiperglicemia — glicemia > 140 mg/dL."""
    vitals = ctx['recent_vitals']

    high_glucose_vs = next(
        (v for v in vitals
         if v.blood_glucose is not None and float(v.blood_glucose) > 140),
        None
    )
    if not high_glucose_vs:
        return None

    return {
        'condition_name': 'Possível Hiperglicemia',
        'severity': 'medium',
        'reason': (
            'Seus registros indicam glicemia acima da meta recomendada (> 140 mg/dL), '
            'o que pode sugerir hiperglicemia gestacional.'
        ),
        'guidance': (
            'Recomenda-se entrar em contato com sua equipe de saúde nas próximas horas. '
            'Este alerta é apenas uma ferramenta de apoio e não substitui avaliação médica.'
        ),
        'symptoms_used': [],
        'vital_signs_used': {
            'Glicemia': f'{float(high_glucose_vs.blood_glucose):.1f} mg/dL',
        },
        'related_vital_sign_obj': high_glucose_vs,
    }


def _rule_uti(ctx):
    """Infecção Urinária — ardência ao urinar + febre ou dor lombar (sem pielonefrite)."""
    symptoms = ctx['recent_symptoms']

    if not _has_symptom(symptoms, 'burning_urination'):
        return None

    has_fever_symptom = _has_symptom(symptoms, 'fever')
    has_lower_back = _has_symptom(symptoms, 'lower_back_pain')

    # Pielonefrite exige todos os três — regra separada cobre isso
    if has_fever_symptom and has_lower_back:
        return None

    if not (has_fever_symptom or has_lower_back):
        return None

    used = _symptom_names(
        symptoms, 'burning_urination', 'fever', 'lower_back_pain'
    )
    return {
        'condition_name': 'Possível Infecção Urinária',
        'severity': 'medium',
        'reason': (
            'Os dados sugerem sintomas compatíveis com infecção urinária, '
            'como ardência ao urinar associada a febre ou dor lombar.'
        ),
        'guidance': (
            'Recomenda-se entrar em contato com sua equipe de saúde nas próximas horas. '
            'Este alerta é apenas uma ferramenta de apoio e não substitui avaliação médica.'
        ),
        'symptoms_used': used,
        'vital_signs_used': {},
        'related_vital_sign_obj': None,
    }


def _rule_pyelonephritis(ctx):
    """Possível Pielonefrite — febre + dor lombar + ardência ao urinar."""
    symptoms = ctx['recent_symptoms']

    if not (
        _has_symptom(symptoms, 'fever')
        and _has_symptom(symptoms, 'lower_back_pain')
        and _has_symptom(symptoms, 'burning_urination')
    ):
        return None

    vitals = ctx['recent_vitals']
    temp_vs = next(
        (v for v in vitals
         if v.temperature_celsius is not None and float(v.temperature_celsius) >= 38),
        None
    )
    used = _symptom_names(
        symptoms, 'fever', 'lower_back_pain', 'burning_urination'
    )
    vital_data = {}
    if temp_vs:
        vital_data['Temperatura'] = f'{float(temp_vs.temperature_celsius):.1f} °C'

    return {
        'condition_name': 'Possível Pielonefrite',
        'severity': 'high',
        'reason': (
            'Seus registros podem indicar uma infecção renal (pielonefrite), '
            'com febre, dor lombar e ardência ao urinar simultâneos.'
        ),
        'guidance': (
            'Procure atendimento médico imediatamente. '
            'Este alerta é apenas uma ferramenta de apoio e não substitui avaliação médica.'
        ),
        'symptoms_used': used,
        'vital_signs_used': vital_data,
        'related_vital_sign_obj': temp_vs,
    }


def _rule_premature_labor(ctx):
    """Trabalho de Parto Prematuro — < 37 semanas + contrações + dor lombar ou abdominal."""
    patient = ctx['patient']
    symptoms = ctx['recent_symptoms']

    try:
        weeks = patient.patient_profile.gestational_age_weeks or 40
    except Exception:
        return None

    if weeks >= 37:
        return None

    if not _has_symptom(symptoms, 'contractions'):
        return None

    if not _has_symptom(symptoms, 'lower_back_pain', 'abdominal_pain'):
        return None

    used = _symptom_names(
        symptoms, 'contractions', 'lower_back_pain', 'abdominal_pain'
    )
    return {
        'condition_name': 'Possível Trabalho de Parto Prematuro',
        'severity': 'high',
        'reason': (
            f'Com {weeks} semanas de gestação, seus registros podem indicar sinais '
            'de trabalho de parto prematuro, como contrações e dor.'
        ),
        'guidance': (
            'Procure atendimento médico imediatamente. '
            'Este alerta é apenas uma ferramenta de apoio e não substitui avaliação médica.'
        ),
        'symptoms_used': used,
        'vital_signs_used': {'Semanas de gestação': str(weeks)},
        'related_vital_sign_obj': None,
    }


def _rule_fetal_distress(ctx):
    """Possível Sofrimento Fetal — redução dos movimentos fetais."""
    symptoms = ctx['recent_symptoms']

    if not _has_symptom(symptoms, 'reduced_fetal_movement'):
        return None

    used = _symptom_names(symptoms, 'reduced_fetal_movement')
    return {
        'condition_name': 'Possível Sofrimento Fetal',
        'severity': 'high',
        'reason': (
            'É importante procurar atendimento: redução dos movimentos fetais '
            'pode indicar necessidade de avaliação médica imediata.'
        ),
        'guidance': (
            'Procure atendimento médico imediatamente. '
            'Este alerta é apenas uma ferramenta de apoio e não substitui avaliação médica.'
        ),
        'symptoms_used': used,
        'vital_signs_used': {},
        'related_vital_sign_obj': None,
    }


def _rule_maternal_hypoxia(ctx):
    """Hipóxia Materna — saturação < 95% + falta de ar."""
    vitals = ctx['recent_vitals']
    symptoms = ctx['recent_symptoms']

    low_spo2_vs = next(
        (v for v in vitals if v.oxygen_saturation is not None and v.oxygen_saturation < 95),
        None
    )
    if not low_spo2_vs:
        return None

    if not _has_symptom(symptoms, 'shortness_of_breath'):
        return None

    used = _symptom_names(symptoms, 'shortness_of_breath')
    return {
        'condition_name': 'Possível Hipóxia Materna',
        'severity': 'high',
        'reason': (
            'Seus registros podem indicar saturação de oxigênio abaixo do esperado '
            'associada a falta de ar.'
        ),
        'guidance': (
            'Procure atendimento médico imediatamente. '
            'Este alerta é apenas uma ferramenta de apoio e não substitui avaliação médica.'
        ),
        'symptoms_used': used,
        'vital_signs_used': {
            'Saturação de O₂': f'{low_spo2_vs.oxygen_saturation}%',
        },
        'related_vital_sign_obj': low_spo2_vs,
    }


def _rule_pulmonary_embolism(ctx):
    """Possível Tromboembolismo Pulmonar — dor no peito + falta de ar + FC elevada ou SpO2 baixa."""
    vitals = ctx['recent_vitals']
    symptoms = ctx['recent_symptoms']

    if not (_has_symptom(symptoms, 'chest_pain') and _has_symptom(symptoms, 'shortness_of_breath')):
        return None

    has_tachy = any(v.heart_rate and v.heart_rate >= 100 for v in vitals)
    has_low_spo2 = any(
        v.oxygen_saturation is not None and v.oxygen_saturation < 95 for v in vitals
    )

    if not (has_tachy or has_low_spo2):
        return None

    used = _symptom_names(symptoms, 'chest_pain', 'shortness_of_breath')
    vital_data = {}
    for v in vitals:
        if v.heart_rate and v.heart_rate >= 100:
            vital_data['Frequência cardíaca'] = f'{v.heart_rate} bpm'
            break
    for v in vitals:
        if v.oxygen_saturation and v.oxygen_saturation < 95:
            vital_data['Saturação de O₂'] = f'{v.oxygen_saturation}%'
            break

    hr_vs = next((v for v in vitals if v.heart_rate and v.heart_rate >= 100), None)
    return {
        'condition_name': 'Possível Tromboembolismo Pulmonar',
        'severity': 'high',
        'reason': (
            'Os dados sugerem sintomas compatíveis com tromboembolismo pulmonar, '
            'como dor no peito, falta de ar e alterações circulatórias.'
        ),
        'guidance': (
            'Procure atendimento médico imediatamente. '
            'Este alerta é apenas uma ferramenta de apoio e não substitui avaliação médica.'
        ),
        'symptoms_used': used,
        'vital_signs_used': vital_data,
        'related_vital_sign_obj': hr_vs,
    }


def _rule_systemic_infection(ctx):
    """Infecção Sistêmica — temperatura ≥ 38°C + FC elevada."""
    vitals = ctx['recent_vitals']

    fever_vs = next(
        (v for v in vitals
         if v.temperature_celsius is not None and float(v.temperature_celsius) >= 38),
        None
    )
    if not fever_vs:
        return None

    tachy_vs = next(
        (v for v in vitals if v.heart_rate and v.heart_rate >= 100),
        None
    )
    if not tachy_vs:
        return None

    return {
        'condition_name': 'Possível Infecção Sistêmica',
        'severity': 'medium',
        'reason': (
            'Seus registros podem indicar sinais de infecção sistêmica, '
            'com temperatura elevada e frequência cardíaca acima do esperado.'
        ),
        'guidance': (
            'Recomenda-se entrar em contato com sua equipe de saúde nas próximas horas. '
            'Este alerta é apenas uma ferramenta de apoio e não substitui avaliação médica.'
        ),
        'symptoms_used': [],
        'vital_signs_used': {
            'Temperatura': f'{float(fever_vs.temperature_celsius):.1f} °C',
            'Frequência cardíaca': f'{tachy_vs.heart_rate} bpm',
        },
        'related_vital_sign_obj': fever_vs,
    }


def _rule_placental_abruption(ctx):
    """Descolamento Prematuro da Placenta — sangramento + dor abdominal ou contrações."""
    symptoms = ctx['recent_symptoms']

    if not _has_symptom(symptoms, 'bleeding'):
        return None

    if not _has_symptom(symptoms, 'abdominal_pain', 'contractions'):
        return None

    used = _symptom_names(
        symptoms, 'bleeding', 'abdominal_pain', 'contractions'
    )
    return {
        'condition_name': 'Possível Descolamento Prematuro da Placenta',
        'severity': 'high',
        'reason': (
            'Os dados sugerem sangramento associado a dor abdominal ou contrações, '
            'o que pode indicar descolamento prematuro da placenta.'
        ),
        'guidance': (
            'Procure atendimento médico imediatamente. '
            'Este alerta é apenas uma ferramenta de apoio e não substitui avaliação médica.'
        ),
        'symptoms_used': used,
        'vital_signs_used': {},
        'related_vital_sign_obj': None,
    }


def _rule_placenta_previa(ctx):
    """Placenta Prévia — sangramento SEM dor abdominal."""
    symptoms = ctx['recent_symptoms']

    if not _has_symptom(symptoms, 'bleeding'):
        return None

    # Se há dor abdominal, a regra de DPP cuida
    if _has_symptom(symptoms, 'abdominal_pain', 'contractions'):
        return None

    used = _symptom_names(symptoms, 'bleeding')
    return {
        'condition_name': 'Possível Placenta Prévia',
        'severity': 'high',
        'reason': (
            'Seus registros indicam sangramento sem dor abdominal, '
            'o que pode sugerir placenta prévia.'
        ),
        'guidance': (
            'Procure atendimento médico imediatamente. '
            'Este alerta é apenas uma ferramenta de apoio e não substitui avaliação médica.'
        ),
        'symptoms_used': used,
        'vital_signs_used': {},
        'related_vital_sign_obj': None,
    }


def _rule_hyperemesis(ctx):
    """Hiperêmese Gravídica — náuseas + vômitos recorrentes."""
    symptoms = ctx['recent_symptoms']

    if not (_has_symptom(symptoms, 'nausea') and _has_symptom(symptoms, 'vomiting')):
        return None

    used = _symptom_names(symptoms, 'nausea', 'vomiting')
    return {
        'condition_name': 'Possível Hiperêmese Gravídica',
        'severity': 'medium',
        'reason': (
            'Os dados sugerem náuseas e vômitos frequentes, '
            'que podem ser compatíveis com hiperêmese gravídica.'
        ),
        'guidance': (
            'Recomenda-se entrar em contato com sua equipe de saúde nas próximas horas. '
            'Este alerta é apenas uma ferramenta de apoio e não substitui avaliação médica.'
        ),
        'symptoms_used': used,
        'vital_signs_used': {},
        'related_vital_sign_obj': None,
    }


def _rule_excessive_weight_gain(ctx):
    """Ganho de Peso Excessivo — peso acima do esperado para a idade gestacional."""
    patient = ctx['patient']
    vitals = ctx['recent_vitals']

    try:
        weeks = patient.patient_profile.gestational_age_weeks or 0
        pre_pregnancy_weight = getattr(patient.patient_profile, 'pre_pregnancy_weight_kg', None)
    except Exception:
        return None

    if not weeks or not pre_pregnancy_weight:
        return None

    current_weight_vs = next(
        (v for v in vitals if v.weight_kg is not None), None
    )
    if not current_weight_vs:
        return None

    gain = float(current_weight_vs.weight_kg) - float(pre_pregnancy_weight)
    # Referência IOM: máx ~16 kg total para IMC normal
    # Estimativa simples: ~0.45 kg/semana a partir da 12a semana
    expected_gain = max(0, (weeks - 12) * 0.45) if weeks > 12 else weeks * 0.25
    if gain <= expected_gain + 2:
        return None

    return {
        'condition_name': 'Possível Ganho de Peso Excessivo',
        'severity': 'medium',
        'reason': (
            f'Os dados sugerem ganho de peso de {gain:.1f} kg, '
            f'acima do esperado para {weeks} semanas de gestação.'
        ),
        'guidance': (
            'Recomenda-se entrar em contato com sua equipe de saúde nas próximas horas. '
            'Este alerta é apenas uma ferramenta de apoio e não substitui avaliação médica.'
        ),
        'symptoms_used': [],
        'vital_signs_used': {
            'Peso atual': f'{float(current_weight_vs.weight_kg):.1f} kg',
            'Semanas de gestação': str(weeks),
        },
        'related_vital_sign_obj': current_weight_vs,
    }


# ---------------------------------------------------------------------------
# Registro de todas as regras (ordem importa: mais específicas primeiro)
# ---------------------------------------------------------------------------

CLINICAL_RULES = [
    _rule_preeclampsia,
    _rule_hypertension,
    _rule_hypoglycemia,
    _rule_hyperglycemia,
    _rule_pyelonephritis,
    _rule_uti,
    _rule_premature_labor,
    _rule_fetal_distress,
    _rule_maternal_hypoxia,
    _rule_pulmonary_embolism,
    _rule_systemic_infection,
    _rule_placental_abruption,
    _rule_placenta_previa,
    _rule_hyperemesis,
    _rule_excessive_weight_gain,
]


# ---------------------------------------------------------------------------
# Ponto de entrada principal
# ---------------------------------------------------------------------------

def evaluate_rules(patient, vital_sign=None, symptom=None):
    """
    Avalia todas as regras clínicas e retorna uma lista de dicts de alertas a criar.
    Aplica deduplicação: evita alertas da mesma condição nas últimas 6 horas.
    """
    from apps.monitoring.models import VitalSign, Symptom, ClinicalAlert

    cutoff_24h = timezone.now() - timedelta(hours=24)
    cutoff_6h = timezone.now() - timedelta(hours=6)

    # Coleta registros recentes
    recent_vitals = list(
        VitalSign.objects.filter(patient=patient, recorded_at__gte=cutoff_24h)
        .order_by('-recorded_at')
    )
    # Garante que o sinal vital atual está incluído
    if vital_sign and vital_sign not in recent_vitals:
        recent_vitals.insert(0, vital_sign)

    recent_symptoms = list(
        Symptom.objects.filter(patient=patient, recorded_at__gte=cutoff_24h)
        .order_by('-recorded_at')
    )
    if symptom and symptom not in recent_symptoms:
        recent_symptoms.insert(0, symptom)

    # Condições já alertadas nas últimas 6h (deduplicação)
    recent_condition_names = set(
        ClinicalAlert.objects.filter(
            patient=patient,
            created_at__gte=cutoff_6h,
        ).values_list('condition_name', flat=True)
    )

    ctx = {
        'patient': patient,
        'vital': vital_sign,
        'symptom': symptom,
        'recent_vitals': recent_vitals,
        'recent_symptoms': recent_symptoms,
    }

    results = []
    for rule_fn in CLINICAL_RULES:
        alert_data = rule_fn(ctx)
        if alert_data is None:
            continue
        if alert_data['condition_name'] in recent_condition_names:
            continue
        # Evita duplicar a mesma condição dentro desta avaliação
        already_added = {r['condition_name'] for r in results}
        if alert_data['condition_name'] in already_added:
            continue
        results.append(alert_data)

    return results
