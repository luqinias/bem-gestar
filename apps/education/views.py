"""
Views for educational content library.
Content is personalized based on patient's gestational week and risk profile.
Doctors (with validated CRM) and admins can create/edit/publish content.
"""
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

_TAG = ['education']

from apps.accounts.permissions import IsDoctorOrAdmin
from .models import ContentCategory, EducationalContent
from .serializers import (
    ContentCategorySerializer,
    EducationalContentListSerializer,
    EducationalContentDetailSerializer,
    EducationalContentWriteSerializer,
)


@extend_schema_view(
    get=extend_schema(tags=_TAG, summary='Listar Categorias'),
    post=extend_schema(tags=_TAG, summary='[Médico/Admin] Criar Categoria'),
)
class ContentCategoryListView(generics.ListCreateAPIView):
    """
    GET  /api/education/categories/
    POST /api/education/categories/  — doctor (validated) or admin
    """
    queryset = ContentCategory.objects.all()
    serializer_class = ContentCategorySerializer
    pagination_class = None

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsDoctorOrAdmin()]
        return [IsAuthenticated()]


@extend_schema_view(
    get=extend_schema(tags=_TAG, summary='Listar Conteúdos Educativos', description='Lista os conteúdos educativos. Para pacientes autenticadas, o conteúdo é automaticamente filtrado pela semana gestacional e perfil de risco. Use ?week= para filtro manual.'),
    post=extend_schema(tags=_TAG, summary='[Médico/Admin] Criar Conteúdo Educativo', description='Cria um novo artigo/vídeo/guia na biblioteca educativa. Requer médico com CRM validado ou administrador.'),
)
class EducationalContentListView(generics.ListCreateAPIView):
    """
    GET  /api/education/contents/
    For patients: automatically filtered by their gestational week and risk profile.
    Query params: category, content_type, week
    POST /api/education/contents/  — doctor (validated) or admin
    """
    filterset_fields = ['category', 'content_type', 'target_risk_level']
    search_fields = ['title', 'summary', 'tags']
    ordering_fields = ['week_start', 'created_at']

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsDoctorOrAdmin()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EducationalContentWriteSerializer
        return EducationalContentListSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return EducationalContent.objects.none()

        qs = EducationalContent.objects.filter(is_published=True)
        user = self.request.user

        if user.is_patient:
            # Personalize by gestational week
            try:
                profile = user.patient_profile
                week = profile.gestational_age_weeks
                if week:
                    qs = qs.filter(
                        models_week_filter(week)
                    )
                # Personalize by risk level
                from apps.monitoring.models import RiskScore
                try:
                    latest_score = RiskScore.objects.filter(patient=user).latest()
                    risk_level = latest_score.risk_level
                    # Include 'all' and the specific risk level
                    qs = qs.filter(
                        target_risk_level__in=['all', risk_level]
                    )
                except RiskScore.DoesNotExist:
                    qs = qs.filter(target_risk_level__in=['all', 'low'])
            except Exception:
                pass

        # Apply manual week filter if provided
        week_param = self.request.query_params.get('week')
        if week_param:
            try:
                week = int(week_param)
                from django.db.models import Q
                qs = qs.filter(
                    Q(week_start__isnull=True) | Q(week_start__lte=week),
                    Q(week_end__isnull=True) | Q(week_end__gte=week),
                )
            except ValueError:
                pass

        return qs.select_related('category')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(
            EducationalContentDetailSerializer(instance).data,
            status=status.HTTP_201_CREATED,
        )


def models_week_filter(week):
    """Build Q filter for gestational week range."""
    from django.db.models import Q
    return (
        Q(week_start__isnull=True) | Q(week_start__lte=week)
    ) & (
        Q(week_end__isnull=True) | Q(week_end__gte=week)
    )


@extend_schema_view(
    get=extend_schema(tags=_TAG, summary='Detalhe de Conteúdo Educativo (por ID)'),
    patch=extend_schema(tags=_TAG, summary='[Médico/Admin] Editar Conteúdo Educativo'),
    delete=extend_schema(tags=_TAG, summary='[Médico/Admin] Remover Conteúdo Educativo'),
)
class EducationalContentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/education/contents/{id}/
    PATCH  /api/education/contents/{id}/  — doctor (validated) or admin
    DELETE /api/education/contents/{id}/  — doctor (validated) or admin
    """
    lookup_field = 'pk'

    def get_permissions(self):
        if self.request.method in ('PATCH', 'PUT', 'DELETE'):
            return [IsDoctorOrAdmin()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method in ('PATCH', 'PUT'):
            return EducationalContentWriteSerializer
        return EducationalContentDetailSerializer

    def get_queryset(self):
        if self.request.method in ('PATCH', 'PUT', 'DELETE'):
            return EducationalContent.objects.all()
        return EducationalContent.objects.filter(is_published=True)

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        instance = self.get_object()
        return Response(EducationalContentDetailSerializer(instance).data)


@extend_schema(tags=_TAG, summary='Detalhe de Conteúdo Educativo (por Slug)')
class EducationalContentBySlugView(generics.RetrieveAPIView):
    """
    GET /api/education/contents/slug/{slug}/
    """
    serializer_class = EducationalContentDetailSerializer
    permission_classes = [IsAuthenticated]
    queryset = EducationalContent.objects.filter(is_published=True)
    lookup_field = 'slug'


@extend_schema(
    tags=_TAG,
    summary='Recomendações da Home (2 conteúdos personalizados)',
    description=(
        'Retorna até 2 conteúdos educativos filtrados pela semana gestacional '
        'e perfil de risco da paciente autenticada. '
        'A seleção rotaciona diariamente de forma determinística.'
    ),
)
class HomeRecommendationsView(generics.ListAPIView):
    """
    GET /api/education/contents/home-recommendations/
    Returns up to 2 personalised educational contents for the patient home screen.
    Rotation: deterministic daily shuffle using (patient_id + day_of_year) as seed.
    """
    serializer_class = EducationalContentListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # never paginate — always returns ≤2 items

    def get_queryset(self):
        import random
        import datetime

        user = self.request.user
        qs = EducationalContent.objects.filter(is_published=True)

        if user.is_patient:
            try:
                profile = user.patient_profile
                week = profile.gestational_age_weeks
                if week:
                    qs = qs.filter(models_week_filter(week))

                # Include risk-appropriate content
                from apps.monitoring.models import RiskScore
                try:
                    latest_score = RiskScore.objects.filter(patient=user).latest()
                    risk_level = latest_score.risk_level
                    qs = qs.filter(target_risk_level__in=['all', risk_level])
                except RiskScore.DoesNotExist:
                    qs = qs.filter(target_risk_level__in=['all', 'low'])
            except Exception:
                # If no profile, return general content (no week filter)
                qs = qs.filter(target_risk_level='all')

        # Daily deterministic rotation:
        # Same patient sees same 2 cards all day, different cards next day.
        day_of_year = datetime.date.today().timetuple().tm_yday
        seed = user.id * 1000 + day_of_year
        items = list(qs.select_related('category'))
        random.Random(seed).shuffle(items)
        return items[:2]

