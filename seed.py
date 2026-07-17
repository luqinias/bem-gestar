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
from apps.consultations.models import Consultation, ExamRequest
from apps.ar.models import ARModel
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

nutricao = ContentCategory.objects.get(name='Nutrição na Gestação')
prenatal = ContentCategory.objects.get(name='Pré-natal')
saude_mental = ContentCategory.objects.get(name='Saúde Mental')

contents = [
    {
        'title': 'Alimentação Saudável no 1º Trimestre',
        'slug': 'alimentacao-1o-trimestre',
        'summary': 'Dicas de nutrição essenciais para as primeiras 13 semanas de gravidez.',
        'content': 'Durante o 1º trimestre, é fundamental consumir ácido fólico, ferro e proteínas...',
        'category': nutricao,
        'week_start': 1, 'week_end': 13,
        'target_risk_level': 'all',
    },
    {
        'title': 'Exames do Pré-natal: 2º Trimestre',
        'slug': 'exames-prenatal-2o-trimestre',
        'summary': 'Quais exames são solicitados entre a 14ª e 27ª semana gestacional.',
        'content': 'O 2º trimestre inclui a morfológica do 2º trimestre, hemograma completo...',
        'category': prenatal,
        'week_start': 14, 'week_end': 27,
        'target_risk_level': 'all',
    },
    {
        'title': 'Controle da Pressão na Gestação de Alto Risco',
        'slug': 'controle-pressao-alto-risco',
        'summary': 'Como monitorar e controlar a pressão arterial em gestações de alto risco.',
        'content': 'Gestantes com hipertensão precisam monitorar a PA diariamente...',
        'category': prenatal,
        'week_start': None, 'week_end': None,
        'target_risk_level': 'high',
    },
    {
        'title': 'Ansiedade e Gestação: Cuidando da Saúde Mental',
        'slug': 'ansiedade-gestacao',
        'summary': 'Como reconhecer e lidar com a ansiedade durante a gravidez.',
        'content': 'A gestação é um período de grandes mudanças emocionais...',
        'category': saude_mental,
        'week_start': None, 'week_end': None,
        'target_risk_level': 'all',
    },
]

for data in contents:
    EducationalContent.objects.get_or_create(
        slug=data['slug'],
        defaults=data,
    )

print("  ✅ 4 conteúdos educativos criados")

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

print("\n🕶️ Criando modelos 3D de Realidade Aumentada (AR)...")
if not ARModel.objects.filter(week=20).exists():
    ARModel.objects.create(
        week=20,
        baby_model='ar_models/baby_week_20.glb',
        estimated_height_cm=25.60,
        estimated_weight_grams=300,
        animation='sleep_idle',
        scale=1.00
    )
    print("  ✅ Modelo de AR para Semana 20 criado")

if not ARModel.objects.filter(week=26).exists():
    ARModel.objects.create(
        week=26,
        baby_model='ar_models/baby_week_26.glb',
        estimated_height_cm=35.60,
        estimated_weight_grams=760,
        animation='sleep_idle',
        scale=1.00
    )
    print("  ✅ Modelo de AR para Semana 26 criado")

print("\n🎉 Seed concluído com sucesso!")
print("\nCredenciais de acesso:")
print("  Admin:    admin@bemgestar.com / admin123@  → /admin/")
print("  Médico:   medico@bemgestar.com / medico123@")
print("  Paciente: paciente@bemgestar.com / paciente123@")
