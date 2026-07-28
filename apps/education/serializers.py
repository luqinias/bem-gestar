"""
Serializers for education app.
"""
from django.utils.text import slugify
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


class EducationalContentWriteSerializer(serializers.ModelSerializer):
    """[Médico validado / Admin] Cria ou edita um conteúdo educativo."""
    slug = serializers.SlugField(required=False)

    class Meta:
        model = EducationalContent
        fields = [
            'id', 'title', 'slug', 'summary', 'content', 'content_type',
            'category', 'thumbnail', 'external_url',
            'week_start', 'week_end', 'target_risk_level', 'tags',
            'is_published',
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        if not attrs.get('slug'):
            base = slugify(attrs.get('title') or (self.instance.title if self.instance else ''))
            slug = base
            suffix = 1
            qs = EducationalContent.objects.all()
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            while qs.filter(slug=slug).exists():
                suffix += 1
                slug = f'{base}-{suffix}'
            attrs['slug'] = slug

        week_start = attrs.get('week_start', getattr(self.instance, 'week_start', None))
        week_end = attrs.get('week_end', getattr(self.instance, 'week_end', None))
        if week_start is not None and week_end is not None and week_start > week_end:
            raise serializers.ValidationError(
                {'week_end': 'A semana final deve ser maior ou igual à semana inicial.'}
            )
        return attrs
