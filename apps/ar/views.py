from decimal import Decimal
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.accounts.models import PatientProfile
from .services import find_closest_ar_model, get_growth_estimate, get_spatial_dimensions_estimate, create_ar_telemetry
from .serializers import ARBabyResponseSerializer, ARTelemetrySerializer
from .models import ARModel

_TAG = ['ar']


class ARBabyModelView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=_TAG,
        summary='Obter Modelo 3D do Bebê',
        description='Retorna os detalhes e links dos modelos 3D (GLB/USDZ) do feto com base na semana gestacional da paciente.',
        parameters=[
            OpenApiParameter(name='patient_id', type=int, required=False, description='ID do usuário da paciente (necessário para médicos)'),
            OpenApiParameter(name='week', type=int, required=False, description='Semana específica (para sobresscrever e testar)')
        ],
        responses={200: ARBabyResponseSerializer}
    )
    def get(self, request):
        user = request.user
        target_week = None

        week_param = request.query_params.get('week')
        if week_param:
            try:
                target_week = int(week_param)
            except ValueError:
                return Response({'error': 'Semana inválida.'}, status=status.HTTP_400_BAD_REQUEST)

        # Get week based on user role if not provided manually
        if not target_week:
            if hasattr(user, 'patient_profile'):
                profile = user.patient_profile
                target_week = profile.gestational_age_weeks or 20
            elif hasattr(user, 'doctor_profile'):
                patient_id = request.query_params.get('patient_id')
                if not patient_id:
                    return Response(
                        {'error': 'Médicos precisam fornecer patient_id da paciente.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                try:
                    patient_profile = PatientProfile.objects.get(user_id=patient_id)
                except PatientProfile.DoesNotExist:
                    return Response({'error': 'Paciente não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

                # Security check: verify patient is linked to this doctor
                doctor = user.doctor_profile
                if not doctor.patients.filter(id=patient_profile.id).exists():
                    return Response(
                        {'error': 'Você não tem permissão para visualizar dados desta paciente.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                target_week = patient_profile.gestational_age_weeks or 20
            else:
                target_week = 20

        # Try to find the closest registered AR Model
        ar_model = find_closest_ar_model(target_week)
        
        # Calculate growth curve estimates for the requested target week
        est_height, est_weight = get_growth_estimate(target_week)
        est_spatial = get_spatial_dimensions_estimate(target_week)

        class TransientBabyData:
            def __init__(self, week, height_cm, weight, baby_model, baby_model_usdz, animation, scale,
                         real_length_meters, real_width_meters, real_depth_meters,
                         bounding_box_x, bounding_box_y, bounding_box_z):
                self.week = week
                self.estimated_height_cm = height_cm
                self.estimated_weight_grams = weight
                self.baby_model = baby_model
                self.baby_model_usdz = baby_model_usdz
                self.animation = animation
                self.scale = scale
                self.real_length_meters = real_length_meters
                self.real_width_meters = real_width_meters
                self.real_depth_meters = real_depth_meters
                self.bounding_box_x = bounding_box_x
                self.bounding_box_y = bounding_box_y
                self.bounding_box_z = bounding_box_z

        if not ar_model:
            baby_data = TransientBabyData(
                week=target_week,
                height_cm=est_height,
                weight=est_weight,
                baby_model=None,
                baby_model_usdz=None,
                animation='sleep_idle',
                scale=1.00,
                real_length_meters=est_spatial['real_length_meters'],
                real_width_meters=est_spatial['real_width_meters'],
                real_depth_meters=est_spatial['real_depth_meters'],
                bounding_box_x=est_spatial['bounding_box_x'],
                bounding_box_y=est_spatial['bounding_box_y'],
                bounding_box_z=est_spatial['bounding_box_z'],
            )
        else:
            # Check if this model is an exact match for the target week
            if ar_model.week == target_week:
                baby_data = TransientBabyData(
                    week=target_week,
                    height_cm=ar_model.estimated_height_cm,
                    weight=ar_model.estimated_weight_grams,
                    baby_model=ar_model.baby_model,
                    baby_model_usdz=ar_model.baby_model_usdz,
                    animation=ar_model.animation,
                    scale=ar_model.scale,
                    real_length_meters=ar_model.real_length_meters,
                    real_width_meters=ar_model.real_width_meters,
                    real_depth_meters=ar_model.real_depth_meters,
                    bounding_box_x=ar_model.bounding_box_x,
                    bounding_box_y=ar_model.bounding_box_y,
                    bounding_box_z=ar_model.bounding_box_z,
                )
            else:
                # Scale ratio: target_height / model_height
                model_height = float(ar_model.estimated_height_cm)
                scale_factor = Decimal(str(est_height)) / Decimal(str(model_height)) if model_height > 0 else Decimal('1.00')
                # Multiply by admin defined base scale
                final_scale = scale_factor * ar_model.scale
                
                baby_data = TransientBabyData(
                    week=target_week,
                    height_cm=est_height,
                    weight=est_weight,
                    baby_model=ar_model.baby_model,
                    baby_model_usdz=ar_model.baby_model_usdz,
                    animation=ar_model.animation,
                    scale=final_scale,
                    real_length_meters=est_spatial['real_length_meters'],
                    real_width_meters=est_spatial['real_width_meters'],
                    real_depth_meters=est_spatial['real_depth_meters'],
                    bounding_box_x=est_spatial['bounding_box_x'],
                    bounding_box_y=est_spatial['bounding_box_y'],
                    bounding_box_z=est_spatial['bounding_box_z'],
                )

        serializer = ARBabyResponseSerializer(baby_data, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ARTelemetryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=_TAG,
        summary='Salvar Telemetria de AR',
        description='Registra estatísticas de uso, FPS e possíveis erros de renderização na Realidade Aumentada.',
        request=ARTelemetrySerializer,
        responses={201: ARTelemetrySerializer}
    )
    def post(self, request):
        serializer = ARTelemetrySerializer(data=request.data)
        if serializer.is_valid():
            telemetry = create_ar_telemetry(
                user=request.user,
                time_in_experience_seconds=serializer.validated_data.get('time_in_experience_seconds', 0),
                views_count=serializer.validated_data.get('views_count', 1),
                captures_count=serializer.validated_data.get('captures_count', 0),
                model_used=serializer.validated_data.get('model_used', ''),
                gestational_week=serializer.validated_data.get('gestational_week', 20),
                avg_fps=serializer.validated_data.get('avg_fps', Decimal('60.00')),
                errors_logged=serializer.validated_data.get('errors_logged', ''),
                crashes_count=serializer.validated_data.get('crashes_count', 0)
            )
            response_serializer = ARTelemetrySerializer(telemetry)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
