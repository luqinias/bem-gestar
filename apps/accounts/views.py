"""
Views for accounts app — registration, auth, and profile management.
"""
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import DoctorProfile, PatientProfile
from .serializers import (
    PatientRegisterSerializer,
    DoctorRegisterSerializer,
    CustomTokenObtainPairSerializer,
    UserSerializer,
    UpdateProfileSerializer,
    DoctorProfileSerializer,
)

User = get_user_model()

_AUTH_TAG = ['auth']


@extend_schema(tags=_AUTH_TAG, summary='Cadastro de Paciente', description='Cria uma nova conta de paciente (gestante) com perfil gestacional. Retorna tokens JWT.')
class PatientRegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/patient/
    Register a new patient account with gestational profile.
    """
    queryset = User.objects.all()
    serializer_class = PatientRegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate tokens immediately after registration
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Cadastro realizado com sucesso.',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=_AUTH_TAG, summary='Cadastro de Médico', description='Cria uma nova conta de médico. O CRM será validado pelo administrador antes da liberação das funcionalidades clínicas. Retorna tokens JWT.')
class DoctorRegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/doctor/
    Register a new doctor account. CRM validation will be done by admin.
    """
    queryset = User.objects.all()
    serializer_class = DoctorRegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            'message': (
                'Cadastro realizado com sucesso. '
                'Seu CRM está em processo de validação. '
                'Funcionalidades clínicas serão liberadas após a validação.'
            ),
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=_AUTH_TAG, summary='Login', description='Autentica com email e senha. Retorna tokens de acesso (2h) e refresh (30 dias) + dados do usuário.')
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    POST /api/auth/login/
    Authenticate and receive JWT tokens.
    """
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema_view(
    get=extend_schema(tags=_AUTH_TAG, summary='Meu Perfil', responses={200: UserSerializer}, description='Retorna os dados completos do usuário autenticado incluindo perfil de paciente ou médico.'),
    put=extend_schema(tags=_AUTH_TAG, summary='Atualizar Perfil (completo)', responses={200: UserSerializer}, description='Atualiza todos os campos do perfil do usuário autenticado.'),
    patch=extend_schema(tags=_AUTH_TAG, summary='Atualizar Perfil (parcial)', responses={200: UserSerializer}, description='Atualiza campos específicos do perfil do usuário autenticado.'),
)
class MeView(APIView):
    """
    GET  /api/auth/me/ — return current user profile
    PUT  /api/auth/me/ — update current user profile
    PATCH /api/auth/me/ — partial update
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        return self._update(request)

    def patch(self, request):
        return self._update(request, partial=True)

    def _update(self, request, partial=False):
        serializer = UpdateProfileSerializer(
            request.user, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


@extend_schema(tags=_AUTH_TAG, summary='Logout', description='Invalida o refresh token (blacklist). O access token continuará válido até expirar.')
class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Blacklist the refresh token to invalidate the session.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': 'Token de refresh é obrigatório.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logout realizado com sucesso.'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=_AUTH_TAG, summary='[Médico] Listar Pacientes', description='Lista todas as pacientes vinculadas ao médico autenticado. Requer CRM validado.')
class PatientsListView(generics.ListAPIView):
    """
    GET /api/auth/patients/
    Doctor-only: list patients linked to the requesting doctor.
    """
    serializer_class = UserSerializer

    def get_permissions(self):
        from .permissions import IsValidatedDoctor
        return [IsValidatedDoctor()]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            from django.contrib.auth import get_user_model
            return get_user_model().objects.none()
        doctor_profile = self.request.user.doctor_profile
        return User.objects.filter(
            patient_profile__doctor=doctor_profile,
            is_active=True
        ).select_related('patient_profile')


@extend_schema(tags=_AUTH_TAG, summary='[Médico] Detalhe de Paciente', description='Retorna dados completos de uma paciente vinculada ao médico. Requer CRM validado.')
class PatientDetailView(generics.RetrieveAPIView):
    """
    GET /api/auth/patients/{id}/
    Doctor-only: get a specific patient's data.
    """
    serializer_class = UserSerializer

    def get_permissions(self):
        from .permissions import IsValidatedDoctor
        return [IsValidatedDoctor()]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()
        doctor_profile = self.request.user.doctor_profile
        return User.objects.filter(
            patient_profile__doctor=doctor_profile,
            is_active=True
        )

    def get_object(self):
        obj = super().get_object()
        return obj


@extend_schema(tags=_AUTH_TAG, summary='[Paciente] Vincular Médico', description='Vincula a paciente autenticada a um médico pelo número do CRM. O médico deve ter CRM validado.')
class LinkDoctorView(APIView):
    """
    POST /api/auth/me/link-doctor/
    Patient-only: link themselves to a doctor by CRM.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_patient:
            return Response(
                {'error': 'Apenas pacientes podem vincular médicos.'},
                status=status.HTTP_403_FORBIDDEN
            )
        crm = request.data.get('crm')
        crm_state = request.data.get('crm_state', '')
        if not crm:
            return Response({'error': 'CRM é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            doctor_profile = DoctorProfile.objects.get(
                crm=crm,
                crm_state__iexact=crm_state,
                is_crm_validated=True
            )
        except DoctorProfile.DoesNotExist:
            return Response(
                {'error': 'Médico não encontrado ou CRM não validado.'},
                status=status.HTTP_404_NOT_FOUND
            )

        profile = request.user.patient_profile
        profile.doctor = doctor_profile
        profile.save()
        return Response({
            'message': f'Vinculado ao(à) Dr(a). {doctor_profile.user.name} com sucesso.',
            'doctor': DoctorProfileSerializer(doctor_profile).data,
        })
