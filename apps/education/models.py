"""
Models for educational content library.
Content is personalized by gestational week and risk profile.
"""
from django.db import models


class ContentCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Categoria')
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, verbose_name='Ícone')

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['name']

    def __str__(self):
        return self.name


class EducationalContent(models.Model):
    """
    Educational articles/videos for gestantes.
    Filtered dynamically by gestational week and risk profile.
    """
    class ContentType(models.TextChoices):
        ARTICLE = 'article', 'Artigo'
        VIDEO = 'video', 'Vídeo'
        INFOGRAPHIC = 'infographic', 'Infográfico'
        GUIDE = 'guide', 'Guia'

    class RiskLevel(models.TextChoices):
        ALL = 'all', 'Todos os perfis'
        LOW = 'low', 'Baixo risco'
        MEDIUM = 'medium', 'Médio risco'
        HIGH = 'high', 'Alto risco'
        CRITICAL = 'critical', 'Crítico'

    title = models.CharField(max_length=300, verbose_name='Título')
    slug = models.SlugField(unique=True, max_length=350)
    summary = models.TextField(verbose_name='Resumo')
    content = models.TextField(verbose_name='Conteúdo completo')
    content_type = models.CharField(
        max_length=15, choices=ContentType.choices,
        default=ContentType.ARTICLE, verbose_name='Tipo'
    )
    category = models.ForeignKey(
        ContentCategory, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='contents',
        verbose_name='Categoria'
    )
    thumbnail = models.ImageField(
        upload_to='education/thumbnails/',
        null=True, blank=True, verbose_name='Thumbnail'
    )
    external_url = models.URLField(blank=True, verbose_name='URL externa (vídeo etc.)')

    # Gestational week range (inclusive)
    week_start = models.PositiveSmallIntegerField(
        null=True, blank=True,
        verbose_name='Semana gestacional inicial (inclusive)'
    )
    week_end = models.PositiveSmallIntegerField(
        null=True, blank=True,
        verbose_name='Semana gestacional final (inclusive)'
    )

    # Target risk profile
    target_risk_level = models.CharField(
        max_length=10, choices=RiskLevel.choices,
        default=RiskLevel.ALL, verbose_name='Perfil de risco alvo'
    )

    # Tags for search
    tags = models.CharField(max_length=500, blank=True, verbose_name='Tags (separadas por vírgula)')

    is_published = models.BooleanField(default=True, verbose_name='Publicado')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Conteúdo Educativo'
        verbose_name_plural = 'Conteúdos Educativos'
        ordering = ['week_start', '-created_at']

    def __str__(self):
        return f'[Semana {self.week_start or "?"}-{self.week_end or "?"}] {self.title}'
