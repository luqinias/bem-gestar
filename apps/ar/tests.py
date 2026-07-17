from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import PatientProfile, DoctorProfile
from .models import ARModel, ARTelemetry

User = get_user_model()


class ARBabyTestCase(APITestCase):

    def setUp(self):
        # Create Patient
        self.patient_user = User.objects.create_user(
            email='patient_test@bemgestar.com',
            password='testpassword123',
            name='Test Patient',
            user_type=User.UserType.PATIENT
        )
        self.patient_profile = PatientProfile.objects.create(
            user=self.patient_user,
            gestational_age_weeks=26,
            cpf='111.111.111-11'
        )

        # Create Doctor
        self.doctor_user = User.objects.create_user(
            email='doctor_test@bemgestar.com',
            password='testpassword123',
            name='Test Doctor',
            user_type=User.UserType.DOCTOR
        )
        self.doctor_profile = DoctorProfile.objects.create(
            user=self.doctor_user,
            crm='123456',
            crm_state='SP',
            specialty=DoctorProfile.Specialty.OBSTETRICS
        )

        # Create Unrelated Patient
        self.unrelated_patient_user = User.objects.create_user(
            email='unrelated_patient@bemgestar.com',
            password='testpassword123',
            name='Unrelated Patient',
            user_type=User.UserType.PATIENT
        )
        self.unrelated_patient_profile = PatientProfile.objects.create(
            user=self.unrelated_patient_user,
            gestational_age_weeks=12,
            cpf='222.222.222-22'
        )

        # Link doctor to test patient
        self.doctor_profile.patients.add(self.patient_profile)

        # Create an AR Model record for week 26
        # Use simple char path for tests since no file uploads actually exist in setUp
        self.ar_model = ARModel.objects.create(
            week=26,
            baby_model='ar_models/baby_26.glb',
            baby_model_usdz='ar_models/baby_26.usdz',
            estimated_height_cm=35.0,
            estimated_weight_grams=900,
            real_length_meters=0.350,
            real_width_meters=0.160,
            real_depth_meters=0.140,
            bounding_box_x=0.160,
            bounding_box_y=0.350,
            bounding_box_z=0.140,
            animation='sleep_idle',
            scale=1.00
        )

        self.baby_model_url = reverse('ar:baby-model')
        self.telemetry_url = reverse('ar:telemetry')

    def test_anonymous_user_denied(self):
        """Verify anonymous requests get 401 Unauthorized."""
        response = self.client.get(self.baby_model_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patient_gets_correct_gestational_model(self):
        """Verify patient retrieves the correct model matching their gestational week."""
        self.client.force_authenticate(user=self.patient_user)
        response = self.client.get(self.baby_model_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['week'], 26)
        self.assertEqual(float(response.data['height_cm']), 35.0)
        self.assertEqual(response.data['weight'], 900)
        self.assertEqual(float(response.data['real_length_meters']), 0.350)
        self.assertEqual(float(response.data['real_width_meters']), 0.160)
        self.assertEqual(float(response.data['real_depth_meters']), 0.140)
        self.assertEqual(response.data['bounding_box'], {'x': 0.160, 'y': 0.350, 'z': 0.140})

    def test_manual_week_override(self):
        """Verify passing a manual week parameter overrides profile settings."""
        self.client.force_authenticate(user=self.patient_user)
        response = self.client.get(self.baby_model_url, {'week': 10})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Week 10 has no model, so we expect fallback calculations based on Hadlock growth curve
        self.assertEqual(response.data['week'], 10)
        self.assertEqual(float(response.data['height_cm']), 3.1)
        self.assertEqual(response.data['weight'], 4)
        self.assertEqual(float(response.data['real_length_meters']), 0.031)
        self.assertEqual(float(response.data['real_width_meters']), 0.014)
        self.assertEqual(float(response.data['real_depth_meters']), 0.012)


    def test_doctor_accesses_linked_patient(self):
        """Verify a doctor can retrieve AR details for a linked patient."""
        self.client.force_authenticate(user=self.doctor_user)
        response = self.client.get(self.baby_model_url, {'patient_id': self.patient_user.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['week'], 26)

    def test_doctor_denied_for_unlinked_patient(self):
        """Verify a doctor cannot retrieve AR details for an unrelated patient."""
        self.client.force_authenticate(user=self.doctor_user)
        response = self.client.get(self.baby_model_url, {'patient_id': self.unrelated_patient_user.id})
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_telemetry_log(self):
        """Verify posting telemetry log works correctly."""
        self.client.force_authenticate(user=self.patient_user)
        payload = {
            'time_in_experience_seconds': 45,
            'views_count': 1,
            'captures_count': 3,
            'model_used': 'ar_models/baby_26.glb',
            'gestational_week': 26,
            'avg_fps': 58.50,
            'errors_logged': 'None',
            'crashes_count': 0
        }
        response = self.client.post(self.telemetry_url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ARTelemetry.objects.count(), 1)
        
        telemetry = ARTelemetry.objects.first()
        self.assertEqual(telemetry.user, self.patient_user)
        self.assertEqual(telemetry.captures_count, 3)
        self.assertEqual(float(telemetry.avg_fps), 58.50)
