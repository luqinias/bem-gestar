from rest_framework import serializers
from .models import ARModel, ARTelemetry

class ARModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ARModel
        fields = [
            'id', 'week', 'baby_model', 'baby_model_usdz',
            'estimated_height_cm', 'estimated_weight_grams',
            'real_length_meters', 'real_width_meters', 'real_depth_meters',
            'bounding_box_x', 'bounding_box_y', 'bounding_box_z',
            'animation', 'scale', 'created_at', 'updated_at'
        ]


class ARBabyResponseSerializer(serializers.Serializer):
    week = serializers.IntegerField()
    height_cm = serializers.DecimalField(max_digits=5, decimal_places=2, source='estimated_height_cm')
    weight = serializers.IntegerField(source='estimated_weight_grams')
    baby_model = serializers.SerializerMethodField()
    baby_model_usdz = serializers.SerializerMethodField()
    animation = serializers.CharField()
    scale = serializers.DecimalField(max_digits=5, decimal_places=2)
    real_length_meters = serializers.DecimalField(max_digits=5, decimal_places=3)
    real_width_meters = serializers.DecimalField(max_digits=5, decimal_places=3)
    real_depth_meters = serializers.DecimalField(max_digits=5, decimal_places=3)
    bounding_box = serializers.SerializerMethodField()

    def get_bounding_box(self, obj) -> dict:
        return {
            'x': float(obj.bounding_box_x),
            'y': float(obj.bounding_box_y),
            'z': float(obj.bounding_box_z),
        }

    def get_baby_model(self, obj: ARModel) -> str:
        request = self.context.get('request')
        if obj.baby_model:
            if request:
                return request.build_absolute_uri(obj.baby_model.url)
            return obj.baby_model.url
        return ""

    def get_baby_model_usdz(self, obj: ARModel) -> str:
        request = self.context.get('request')
        if obj.baby_model_usdz:
            if request:
                return request.build_absolute_uri(obj.baby_model_usdz.url)
            return obj.baby_model_usdz.url
        return ""


class ARTelemetrySerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = ARTelemetry
        fields = [
            'id', 'user', 'user_email', 'time_in_experience_seconds',
            'views_count', 'captures_count', 'model_used',
            'gestational_week', 'avg_fps', 'errors_logged',
            'crashes_count', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'user_email', 'created_at']
