"""
Serializers for messaging app.
"""
from rest_framework import serializers
from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.name', read_only=True)
    sender_type = serializers.CharField(source='sender.user_type', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'sender', 'sender_name', 'sender_type',
            'content', 'status', 'status_display', 'read', 'read_at',
            'attachment', 'sent_at', 'created_at',
        ]
        read_only_fields = ['id', 'sender', 'conversation', 'read', 'read_at', 'created_at']


class SendMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['content', 'status', 'sent_at', 'attachment']
        extra_kwargs = {
            'sent_at': {'required': False},
            'status': {'required': False},
        }


class ConversationSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)
    patient_avatar = serializers.ImageField(source='patient.avatar', read_only=True)
    doctor_avatar = serializers.ImageField(source='doctor.avatar', read_only=True)
    last_message = MessageSerializer(read_only=True)
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id', 'patient', 'patient_name', 'patient_avatar',
            'doctor', 'doctor_name', 'doctor_avatar',
            'last_message', 'unread_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'patient', 'doctor', 'created_at', 'updated_at']

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request:
            return obj.unread_count(request.user)
        return 0
