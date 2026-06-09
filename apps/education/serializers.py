"""
Serializers for education app.
"""
from rest_framework import serializers
from .models import ContentCategory, EducationalContent


class ContentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentCategory
        fields = ['id', 'name', 'description', 'icon']


class EducationalContentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    content_type_display = serializers.CharField(source='get_content_type_display', read_only=True)

    class Meta:
        model = EducationalContent
        fields = [
            'id', 'title', 'slug', 'summary', 'content_type', 'content_type_display',
            'category', 'category_name', 'thumbnail', 'external_url',
            'week_start', 'week_end', 'target_risk_level', 'tags',
            'created_at',
        ]


class EducationalContentDetailSerializer(EducationalContentListSerializer):
    """Full serializer for detail view."""
    class Meta(EducationalContentListSerializer.Meta):
        fields = EducationalContentListSerializer.Meta.fields + ['content', 'updated_at']
