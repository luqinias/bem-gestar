"""
Views for educational content library.
Content is personalized based on patient's gestational week and risk profile.
"""
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

_TAG = ['education']

from apps.accounts.permissions import IsPatient
from .models import ContentCategory, EducationalContent
from .serializers import ContentCategorySerializer, EducationalContentListSerializer, EducationalContentDetailSerializer


@extend_schema(tags=_TAG, summary='Listar Categorias')
class ContentCategoryListView(generics.ListAPIView):
    """
    GET /api/education/categories/
    """
    queryset = ContentCategory.objects.all()
    serializer_class = ContentCategorySerializer
    permission_classes = [IsAuthenticated]


@extend_schema(tags=_TAG, summary='Listar Conteúdos Educativos', description='Lista os conteúdos educativos. Para pacientes autenticadas, o conteúdo é automaticamente filtrado pela semana gestacional e perfil de risco. Use ?week= para filtro manual.')
class EducationalContentListView(generics.ListAPIView):
    """
    GET /api/education/contents/
    For patients: automatically filtered by their gestational week and risk profile.
    Query params: category, content_type, week
    """
    serializer_class = EducationalContentListSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['category', 'content_type', 'target_risk_level']
    search_fields = ['title', 'summary', 'tags']
    ordering_fields = ['week_start', 'created_at']

    def get_queryset(self):
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


def models_week_filter(week):
    """Build Q filter for gestational week range."""
    from django.db.models import Q
    return (
        Q(week_start__isnull=True) | Q(week_start__lte=week)
    ) & (
        Q(week_end__isnull=True) | Q(week_end__gte=week)
    )


@extend_schema(tags=_TAG, summary='Detalhe de Conteúdo Educativo (por ID)')
class EducationalContentDetailView(generics.RetrieveAPIView):
    """
    GET /api/education/contents/{id}/
    GET /api/education/contents/{slug}/  — also accessible by slug
    """
    serializer_class = EducationalContentDetailSerializer
    permission_classes = [IsAuthenticated]
    queryset = EducationalContent.objects.filter(is_published=True)
    lookup_field = 'pk'


@extend_schema(tags=_TAG, summary='Detalhe de Conteúdo Educativo (por Slug)')
class EducationalContentBySlugView(generics.RetrieveAPIView):
    """
    GET /api/education/contents/slug/{slug}/
    """
    serializer_class = EducationalContentDetailSerializer
    permission_classes = [IsAuthenticated]
    queryset = EducationalContent.objects.filter(is_published=True)
    lookup_field = 'slug'
