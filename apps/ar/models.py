from django.db import models
from django.conf import settings

class ARModel(models.Model):
    """
    Saves metadata and 3D files (GLB & USDZ) of the fetus for each gestational week.
    """
    week = models.PositiveSmallIntegerField(unique=True, verbose_name="Semana Gestacional")
    baby_model = models.FileField(upload_to='ar_models/', verbose_name="Modelo 3D (GLB)")
    baby_model_usdz = models.FileField(upload_to='ar_models/', blank=True, null=True, verbose_name="Modelo 3D (USDZ)")
    
    # Growth curves / Medical data estimates
    estimated_height_cm = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Comprimento Estimado (cm)")
    estimated_weight_grams = models.PositiveIntegerField(verbose_name="Peso Estimado (g)")
    
    # True AR Physical Dimensions
    real_length_meters = models.DecimalField(max_digits=5, decimal_places=3, default=0.000, verbose_name="Comprimento Real (m)")
    real_width_meters = models.DecimalField(max_digits=5, decimal_places=3, default=0.000, verbose_name="Largura Real (m)")
    real_depth_meters = models.DecimalField(max_digits=5, decimal_places=3, default=0.000, verbose_name="Profundidade Real (m)")
    
    # Bounding Box Coordinates
    bounding_box_x = models.DecimalField(max_digits=5, decimal_places=3, default=0.000, verbose_name="Bounding Box X")
    bounding_box_y = models.DecimalField(max_digits=5, decimal_places=3, default=0.000, verbose_name="Bounding Box Y")
    bounding_box_z = models.DecimalField(max_digits=5, decimal_places=3, default=0.000, verbose_name="Bounding Box Z")
    
    # Default settings for the experience
    animation = models.CharField(max_length=100, default='sleep_idle', verbose_name="Animação Padrão")
    scale = models.DecimalField(max_digits=5, decimal_places=2, default=1.00, verbose_name="Escala do Modelo")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Modelo do Bebê em RA"
        verbose_name_plural = "Modelos do Bebê em RA"
        ordering = ['week']

    def __str__(self):
        return f"Semana {self.week} — {self.estimated_height_cm}cm / {self.estimated_weight_grams}g"


class ARTelemetry(models.Model):
    """
    Tracks analytical data and crashes/telemetry from the AR baby experience.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ar_telemetries',
        verbose_name="Usuário"
    )
    time_in_experience_seconds = models.PositiveIntegerField(default=0, verbose_name="Tempo na Experiência (s)")
    views_count = models.PositiveIntegerField(default=1, verbose_name="Visualizações")
    captures_count = models.PositiveIntegerField(default=0, verbose_name="Capturas de Foto")
    model_used = models.CharField(max_length=255, verbose_name="Modelo Utilizado")
    gestational_week = models.PositiveSmallIntegerField(verbose_name="Semana Gestacional")
    avg_fps = models.DecimalField(max_digits=5, decimal_places=2, default=60.00, verbose_name="FPS Médio")
    errors_logged = models.TextField(blank=True, verbose_name="Erros/Logs de Dispositivo")
    crashes_count = models.PositiveSmallIntegerField(default=0, verbose_name="Quedas de Execução")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Registrado em")

    class Meta:
        verbose_name = "Telemetria de RA"
        verbose_name_plural = "Telemetrias de RA"
        ordering = ['-created_at']

    def __str__(self):
        return f"Telemetria {self.user.email} — Semana {self.gestational_week} em {self.created_at.strftime('%d/%m/%Y %H:%M')}"
