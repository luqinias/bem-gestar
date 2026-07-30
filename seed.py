"""
Seed script: creates initial data for development/testing.
Run with: python manage.py shell < seed.py
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bemgestar.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.accounts.models import PatientProfile, DoctorProfile
from apps.education.models import ContentCategory, EducationalContent
from apps.consultations.models import Consultation, ExamRequest, Prescription
from apps.monitoring.models import VitalSign, Symptom, RiskScore
from apps.monitoring.services import calculate_risk_score, check_and_create_alerts
from django.utils import timezone
from datetime import date, timedelta

User = get_user_model()

print("🌱 Criando superusuário admin...")
if not User.objects.filter(email='admin@bemgestar.com').exists():
    User.objects.create_superuser(
        email='admin@bemgestar.com',
        name='Administrador BemGestar',
        password='admin123@',
    )
    print("  ✅ admin@bemgestar.com / admin123@")

print("\n🩺 Criando médico de teste...")
if not User.objects.filter(email='medico@bemgestar.com').exists():
    doctor_user = User.objects.create_user(
        email='medico@bemgestar.com',
        name='Dra. Ana Lima',
        password='medico123@',
        user_type='doctor',
    )
    DoctorProfile.objects.create(
        user=doctor_user,
        crm='123456',
        crm_state='SP',
        specialty='obstetrics',
        institution='Hospital Maternidade Bem-Estar',
        is_crm_validated=True,
    )
    print("  ✅ medico@bemgestar.com / medico123@  (CRM validado)")

print("\n🤰 Criando paciente de teste...")
if not User.objects.filter(email='paciente@bemgestar.com').exists():
    patient_user = User.objects.create_user(
        email='paciente@bemgestar.com',
        name='Maria Silva',
        password='paciente123@',
        user_type='patient',
        phone='(11) 99999-1234',
        date_of_birth=date(1995, 3, 15),
    )
    doctor_profile = DoctorProfile.objects.get(crm='123456')
    PatientProfile.objects.create(
        user=patient_user,
        gestational_age_weeks=24,
        expected_delivery_date=date.today() + timedelta(weeks=16),
        last_menstrual_period=date.today() - timedelta(weeks=24),
        blood_type='O+',
        height_cm=162.5,
        pre_gestational_weight_kg=60.0,
        doctor=doctor_profile,
    )
    print("  ✅ paciente@bemgestar.com / paciente123@  (vinculada à Dra. Ana Lima)")

print("\n🩺 Criando médico com CRM pendente de validação (para testar o painel admin)...")
if not User.objects.filter(email='medico.pendente@bemgestar.com').exists():
    pending_doctor_user = User.objects.create_user(
        email='medico.pendente@bemgestar.com',
        name='Dr. João Souza',
        password='medico123@',
        user_type='doctor',
    )
    DoctorProfile.objects.create(
        user=pending_doctor_user,
        crm='654321',
        crm_state='RJ',
        specialty='gynecology',
        institution='Clínica Vida Nova',
        is_crm_validated=False,
    )
    print("  ✅ medico.pendente@bemgestar.com / medico123@  (CRM aguardando validação)")

print("\n🤰 Criando paciente sem médico vinculado (para testar vínculo pelo admin)...")
if not User.objects.filter(email='paciente.semvinculo@bemgestar.com').exists():
    unlinked_patient_user = User.objects.create_user(
        email='paciente.semvinculo@bemgestar.com',
        name='Júlia Costa',
        password='paciente123@',
        user_type='patient',
        phone='(11) 98888-4321',
        date_of_birth=date(1998, 7, 22),
    )
    PatientProfile.objects.create(
        user=unlinked_patient_user,
        gestational_age_weeks=10,
        expected_delivery_date=date.today() + timedelta(weeks=30),
        last_menstrual_period=date.today() - timedelta(weeks=10),
        blood_type='A+',
        height_cm=168.0,
        pre_gestational_weight_kg=58.0,
        doctor=None,
    )
    print("  ✅ paciente.semvinculo@bemgestar.com / paciente123@  (sem médico vinculado)")

print("\n📚 Criando categorias e conteúdos educativos...")
categories = [
    ('Nutrição na Gestação', 'Alimentação saudável durante a gravidez', '🥗'),
    ('Exercícios e Movimento', 'Atividade física segura para gestantes', '🏃‍♀️'),
    ('Saúde Mental', 'Bem-estar emocional e psicológico', '🧠'),
    ('Pré-natal', 'Consultas e exames do pré-natal', '🩺'),
    ('Preparação para o Parto', 'O que esperar do trabalho de parto', '👶'),
    ('Amamentação', 'Tudo sobre amamentação e aleitamento', '🍼'),
]

for name, desc, icon in categories:
    ContentCategory.objects.get_or_create(name=name, defaults={'description': desc, 'icon': icon})

print("  ✅ 6 categorias criadas")

nutricao     = ContentCategory.objects.get(name='Nutrição na Gestação')
prenatal     = ContentCategory.objects.get(name='Pré-natal')
saude_mental = ContentCategory.objects.get(name='Saúde Mental')
exercicios   = ContentCategory.objects.get(name='Exercícios e Movimento')
parto        = ContentCategory.objects.get(name='Preparação para o Parto')
amamentacao  = ContentCategory.objects.get(name='Amamentação')

contents = [
    # ── 1º Trimestre (semanas 1–13) ──────────────────────────────
    {
        'title': 'Alimentação Saudável no 1º Trimestre',
        'slug': 'alimentacao-1o-trimestre',
        'summary': 'Dicas de nutrição essenciais para as primeiras 13 semanas de gravidez.',
        'content': 'Durante o 1º trimestre, é fundamental consumir ácido fólico, ferro e proteínas. Priorize folhas verde-escuras, feijão, ovos e carnes magras. O ácido fólico é especialmente importante nas primeiras semanas para prevenir defeitos no tubo neural do bebê.',
        'category': nutricao,
        'week_start': 1, 'week_end': 13,
        'target_risk_level': 'all',
    },
    {
        'title': 'Enjoos na Gravidez: Como Aliviar',
        'slug': 'enjoos-gravidez',
        'summary': 'Estratégias práticas para lidar com as náuseas do início da gestação.',
        'content': 'As náuseas matinais são comuns no 1º trimestre. Coma pequenas porções a cada 2–3 horas e evite odores fortes. Gengibre em chá ou biscoito pode ajudar. Se os enjoos forem intensos e persistentes, informe sua equipe de saúde.',
        'category': nutricao,
        'week_start': 1, 'week_end': 13,
        'target_risk_level': 'all',
    },
    {
        'title': 'Sua Primeira Consulta de Pré-natal',
        'slug': 'primeira-consulta-prenatal',
        'summary': 'O que esperar e como se preparar para a primeira consulta gestacional.',
        'content': 'Na primeira consulta o médico confirma a gestação, calcula a data provável do parto e solicita exames de rotina (hemograma, tipagem sanguínea, glicemia, urina e infecções). Leve documentos e anote suas dúvidas com antecedência.',
        'category': prenatal,
        'week_start': 1, 'week_end': 13,
        'target_risk_level': 'all',
    },
    {
        'title': 'Ácido Fólico: Por que é Tão Importante',
        'slug': 'acido-folico-gestacao',
        'summary': 'A importância da suplementação de ácido fólico desde antes da gravidez.',
        'content': 'O ácido fólico (vitamina B9) é essencial para a formação do sistema nervoso do bebê. A suplementação deve começar pelo menos 3 meses antes da gestação e continuar até o fim do 1º trimestre. A dose usual é de 400 a 800 mcg/dia conforme orientação médica.',
        'category': nutricao,
        'week_start': 1, 'week_end': 13,
        'target_risk_level': 'all',
    },

    # ── 2º Trimestre (semanas 14–27) ─────────────────────────────
    {
        'title': 'Exames do Pré-natal: 2º Trimestre',
        'slug': 'exames-prenatal-2o-trimestre',
        'summary': 'Quais exames são solicitados entre a 14ª e 27ª semana gestacional.',
        'content': 'O 2º trimestre inclui a ultrassonografia morfológica (entre 20–24 semanas), hemograma completo, glicemia de jejum e o teste de tolerância à glicose (entre 24–28 semanas). Esses exames avaliam o desenvolvimento fetal e rastreiam diabetes gestacional.',
        'category': prenatal,
        'week_start': 14, 'week_end': 27,
        'target_risk_level': 'all',
    },
    {
        'title': 'Exercícios Seguros para Gestantes',
        'slug': 'exercicios-seguros-gestantes',
        'summary': 'Atividades físicas recomendadas e como praticar com segurança na gravidez.',
        'content': 'Caminhadas leves, hidroginástica e yoga para gestantes são ótimas opções no 2º trimestre. A atividade física melhora a circulação, reduz inchaços e favorece o bem-estar emocional. Evite atividades de impacto e sempre converse com sua equipe de saúde antes de iniciar.',
        'category': exercicios,
        'week_start': 14, 'week_end': 27,
        'target_risk_level': 'all',
    },
    {
        'title': 'Movimentos do Bebê: Quando Sentir e O Que Observar',
        'slug': 'movimentos-fetais',
        'summary': 'Entenda quando os movimentos fetais começam e como monitorá-los.',
        'content': 'A maioria das gestantes começa a sentir movimentos entre a 18ª e 22ª semana. No 3º trimestre, o bebê deve apresentar pelo menos 10 movimentos em 2 horas. Diminuição dos movimentos deve ser comunicada ao médico imediatamente.',
        'category': prenatal,
        'week_start': 14, 'week_end': 27,
        'target_risk_level': 'all',
    },
    {
        'title': 'Ganho de Peso Saudável na Gestação',
        'slug': 'ganho-peso-gestacao',
        'summary': 'Quanto é saudável ganhar de peso durante a gravidez?',
        'content': 'O ganho de peso ideal varia conforme o IMC pré-gestacional. Gestantes com peso adequado devem ganhar entre 11 e 16 kg ao longo de toda a gestação. Não faça dietas restritivas — converse com um nutricionista para orientação individualizada.',
        'category': nutricao,
        'week_start': 14, 'week_end': 27,
        'target_risk_level': 'all',
    },

    # ── 3º Trimestre (semanas 28–42) ─────────────────────────────
    {
        'title': 'Preparação para o Trabalho de Parto',
        'slug': 'preparacao-trabalho-parto',
        'summary': 'Sinais do início do trabalho de parto e quando ir à maternidade.',
        'content': 'Os sinais incluem contrações regulares a cada 5 minutos, perda do tampão mucoso e ruptura da bolsa. Prepare sua bolsa de maternidade com antecedência. Se tiver dúvidas, entre em contato com sua equipe médica.',
        'category': parto,
        'week_start': 28, 'week_end': 42,
        'target_risk_level': 'all',
    },
    {
        'title': 'Enxoval do Bebê: O Essencial para o Início',
        'slug': 'enxoval-bebe-essencial',
        'summary': 'Lista com os itens indispensáveis para os primeiros dias do recém-nascido.',
        'content': 'Para os primeiros dias você precisará de body e macacão (tamanho P e M), fraldas, lenços umedecidos, cueiros, banheira e pomada para assaduras. Evite comprar em excesso antes do nascimento — o tamanho do bebê pode surpreender.',
        'category': parto,
        'week_start': 28, 'week_end': 42,
        'target_risk_level': 'all',
    },
    {
        'title': 'Amamentação: Primeiros Passos',
        'slug': 'amamentacao-primeiros-passos',
        'summary': 'Como se preparar para o aleitamento materno ainda na gestação.',
        'content': 'O leite materno oferece proteção imunológica e nutrição completa ao recém-nascido. Na gestação, informe-se sobre pega correta e posições de amamentação. Grupos de apoio ao aleitamento podem ajudar muito no início.',
        'category': amamentacao,
        'week_start': 28, 'week_end': 42,
        'target_risk_level': 'all',
    },
    {
        'title': 'Desconfortos do 3º Trimestre e Como Aliviar',
        'slug': 'desconfortos-3o-trimestre',
        'summary': 'Dores lombares, inchaços e insônia: estratégias para o fim da gestação.',
        'content': 'No 3º trimestre são comuns dores lombares, inchaço nas pernas, azia e dificuldade para dormir. Use travesseiro entre os joelhos ao deitar, eleve os pés e reduza o sódio para o inchaço. Para a azia, evite refeições volumosas à noite.',
        'category': exercicios,
        'week_start': 28, 'week_end': 42,
        'target_risk_level': 'all',
    },

    # ── Conteúdos gerais (qualquer semana) ───────────────────────
    {
        'title': 'Ansiedade e Gestação: Cuidando da Saúde Mental',
        'slug': 'ansiedade-gestacao',
        'summary': 'Como reconhecer e lidar com a ansiedade durante a gravidez.',
        'content': 'A gestação é um período de grandes mudanças emocionais. Sentir ansiedade é normal, mas quando persiste e atrapalha o dia a dia, é importante buscar ajuda. Acompanhamento psicológico durante a gestação é seguro e muito benéfico.',
        'category': saude_mental,
        'week_start': None, 'week_end': None,
        'target_risk_level': 'all',
    },
    {
        'title': 'Hidratação na Gestação',
        'slug': 'hidratacao-gestacao',
        'summary': 'A importância de se manter hidratada durante toda a gravidez.',
        'content': 'Durante a gestação a necessidade de líquidos aumenta. O ideal é consumir cerca de 2 a 3 litros de água por dia. A boa hidratação previne infecções urinárias, melhora a circulação e contribui para a saúde do líquido amniótico.',
        'category': nutricao,
        'week_start': None, 'week_end': None,
        'target_risk_level': 'all',
    },
    {
        'title': 'Sono na Gestação: Dicas para Noites Mais Tranquilas',
        'slug': 'sono-gestacao',
        'summary': 'Como dormir melhor durante a gravidez em cada trimestre.',
        'content': 'Dormir de lado (preferencialmente do lado esquerdo) é recomendado a partir do 2º trimestre para melhorar a circulação. Use travesseiros de suporte para a barriga e entre os joelhos. Evite telas antes de dormir e mantenha horários regulares.',
        'category': saude_mental,
        'week_start': None, 'week_end': None,
        'target_risk_level': 'all',
    },
    {
        'title': 'Controle da Pressão na Gestação de Alto Risco',
        'slug': 'controle-pressao-alto-risco',
        'summary': 'Como monitorar e controlar a pressão arterial em gestações de alto risco.',
        'content': 'Gestantes com hipertensão precisam monitorar a PA diariamente. Sinais de alerta: PA acima de 140/90 mmHg, inchaço repentino, dor de cabeça intensa e visão turva. Nesses casos procure atendimento médico imediatamente.',
        'category': prenatal,
        'week_start': None, 'week_end': None,
        'target_risk_level': 'high',
    },
]

created_count = 0
for data in contents:
    _, created = EducationalContent.objects.get_or_create(
        slug=data['slug'],
        defaults=data,
    )
    if created:
        created_count += 1

print(f'  16 conteudos educativos configurados ({created_count} novo(s), {EducationalContent.objects.count()} total)')

print("\n📅 Criando consultas de teste...")
patient_user = User.objects.get(email='paciente@bemgestar.com')
doctor_user = User.objects.get(email='medico@bemgestar.com')

# scheduled tomorrow at 09:30
tomorrow = timezone.now().replace(hour=9, minute=30, second=0, microsecond=0) + timedelta(days=1)
if not Consultation.objects.filter(patient=patient_user, scheduled_date=tomorrow).exists():
    Consultation.objects.create(
        patient=patient_user,
        doctor=doctor_user,
        scheduled_date=tomorrow,
        consultation_type=Consultation.ConsultationType.IN_PERSON,
        location="Clínica BemGestar - Unidade Sul",
        notes="Primeira consulta de retorno do segundo trimestre.",
        status=Consultation.Status.SCHEDULED,
    )
    print("  ✅ Consulta agendada criada para amanhã às 09:30")

# completed last week
last_week = timezone.now().replace(hour=14, minute=0, second=0, microsecond=0) - timedelta(days=7)
if not Consultation.objects.filter(patient=patient_user, scheduled_date=last_week).exists():
    Consultation.objects.create(
        patient=patient_user,
        doctor=doctor_user,
        scheduled_date=last_week,
        consultation_type=Consultation.ConsultationType.IN_PERSON,
        location="Hospital Maternidade",
        notes="Acompanhamento mensal de rotina.",
        status=Consultation.Status.COMPLETED,
    )
    print("  ✅ Consulta realizada criada (semana passada)")

print("\n🧪 Criando solicitações de exame de teste...")
if not ExamRequest.objects.filter(patient=patient_user, exam_name="Ultrassom morfológico").exists():
    ExamRequest.objects.create(
        patient=patient_user,
        doctor=doctor_user,
        exam_name="Ultrassom morfológico",
        clinical_indication="Avaliação anatômica fetal do segundo trimestre.",
        priority=ExamRequest.Priority.ROUTINE,
        status=ExamRequest.Status.PENDING,
        notes="Realizar jejum leve se indicado pelo laboratório.",
    )
    print("  ✅ Solicitação de Ultrassom morfológico (Pendente) criada")

if not ExamRequest.objects.filter(patient=patient_user, exam_name="Exame de sangue").exists():
    ExamRequest.objects.create(
        patient=patient_user,
        doctor=doctor_user,
        exam_name="Exame de sangue",
        clinical_indication="Hemograma completo e curva glicêmica.",
        priority=ExamRequest.Priority.URGENT,
        status=ExamRequest.Status.PENDING,
        notes="Jejum de 8 horas obrigatório.",
    )
    print("  ✅ Solicitação de Exame de sangue (Pendente) criada")

print("\n💊 Criando receita digital de teste...")
if not Prescription.objects.filter(patient=patient_user, title="Ácido fólico 5mg").exists():
    Prescription.objects.create(
        patient=patient_user,
        doctor=doctor_user,
        prescription_type=Prescription.PrescriptionType.MEDICATION,
        title="Ácido fólico 5mg",
        content="Ácido fólico 5mg — 1 comprimido ao dia.",
        instructions="Tomar 1 comprimido ao dia, preferencialmente após o café da manhã.",
        valid_until=date.today() + timedelta(days=90),
    )
    print("  ✅ Receita de Ácido fólico 5mg criada")

print("\n📈 Criando histórico de sinais vitais e sintomas (para os gráficos de acompanhamento)...")
if not VitalSign.objects.filter(patient=patient_user).exists():
    # Últimos 5 registros, do mais antigo para o mais recente, com uma leve
    # elevação de pressão no penúltimo registro para gerar um alerta de exemplo.
    vitals_history = [
        {'days_ago': 12, 'systolic_bp': 112, 'diastolic_bp': 72, 'heart_rate': 78, 'temperature_celsius': 36.5, 'weight_kg': 61.2, 'oxygen_saturation': 98, 'blood_glucose': 88},
        {'days_ago': 9,  'systolic_bp': 115, 'diastolic_bp': 74, 'heart_rate': 80, 'temperature_celsius': 36.6, 'weight_kg': 61.5, 'oxygen_saturation': 98, 'blood_glucose': 91},
        {'days_ago': 6,  'systolic_bp': 118, 'diastolic_bp': 76, 'heart_rate': 82, 'temperature_celsius': 36.7, 'weight_kg': 61.8, 'oxygen_saturation': 97, 'blood_glucose': 94},
        {'days_ago': 3,  'systolic_bp': 142, 'diastolic_bp': 91, 'heart_rate': 88, 'temperature_celsius': 36.8, 'weight_kg': 62.0, 'oxygen_saturation': 97, 'blood_glucose': 105},
        {'days_ago': 1,  'systolic_bp': 121, 'diastolic_bp': 78, 'heart_rate': 81, 'temperature_celsius': 36.6, 'weight_kg': 62.1, 'oxygen_saturation': 98, 'blood_glucose': 92},
    ]
    for entry in vitals_history:
        recorded_at = timezone.now().replace(hour=8, minute=0, second=0, microsecond=0) - timedelta(days=entry['days_ago'])
        vital_sign = VitalSign.objects.create(
            patient=patient_user,
            recorded_at=recorded_at,
            systolic_bp=entry['systolic_bp'],
            diastolic_bp=entry['diastolic_bp'],
            heart_rate=entry['heart_rate'],
            temperature_celsius=entry['temperature_celsius'],
            weight_kg=entry['weight_kg'],
            oxygen_saturation=entry['oxygen_saturation'],
            blood_glucose=entry['blood_glucose'],
        )
        result = calculate_risk_score(vital_sign=vital_sign, patient=patient_user)
        risk_score_obj = RiskScore.objects.create(
            patient=patient_user,
            score=result['score'],
            risk_level=result['risk_level'],
            contributing_factors=result['contributing_factors'],
        )
        check_and_create_alerts(vital_sign=vital_sign, patient=patient_user, risk_score_obj=risk_score_obj)
    print(f"  ✅ {len(vitals_history)} registros de sinais vitais criados (com score de risco e alertas)")

if not Symptom.objects.filter(patient=patient_user).exists():
    symptoms_history = [
        {'days_ago': 8, 'symptom_type': 'nausea', 'severity': Symptom.Severity.MILD, 'description': 'Enjoo leve pela manhã.'},
        {'days_ago': 5, 'symptom_type': 'lower_back_pain', 'severity': Symptom.Severity.MODERATE, 'description': 'Dor lombar ao final do dia.'},
        {'days_ago': 3, 'symptom_type': 'swelling', 'severity': Symptom.Severity.MILD, 'description': 'Leve inchaço nos pés.'},
    ]
    for entry in symptoms_history:
        recorded_at = timezone.now().replace(hour=20, minute=0, second=0, microsecond=0) - timedelta(days=entry['days_ago'])
        symptom = Symptom.objects.create(
            patient=patient_user,
            recorded_at=recorded_at,
            symptom_type=entry['symptom_type'],
            severity=entry['severity'],
            description=entry['description'],
        )
        result = calculate_risk_score(symptom=symptom, patient=patient_user)
        risk_score_obj = RiskScore.objects.create(
            patient=patient_user,
            score=result['score'],
            risk_level=result['risk_level'],
            contributing_factors=result['contributing_factors'],
        )
        check_and_create_alerts(symptom=symptom, patient=patient_user, risk_score_obj=risk_score_obj)
    print(f"  ✅ {len(symptoms_history)} registros de sintomas criados")

print("\n🎉 Seed concluído com sucesso!")
print("\nCredenciais de acesso:")
print("  Admin:               admin@bemgestar.com / admin123@  → /admin/")
print("  Médico (validado):   medico@bemgestar.com / medico123@  (Dra. Ana Lima)")
print("  Médico (pendente):   medico.pendente@bemgestar.com / medico123@  (Dr. João Souza — CRM aguardando validação)")
print("  Paciente (vinculada): paciente@bemgestar.com / paciente123@  (Maria Silva)")
print("  Paciente (sem vínculo): paciente.semvinculo@bemgestar.com / paciente123@  (Júlia Costa)")
