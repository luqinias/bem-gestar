"""
Views for messaging app.
"""
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsPatientOrValidatedDoctor
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer, SendMessageSerializer

_TAG = ['messaging']

User = get_user_model()


@extend_schema(tags=_TAG, summary='Listar Conversas', description='Lista todas as conversas do usuário autenticado com o último mensagem e contagem de não lidas.')
class ConversationListView(generics.ListAPIView):
    """
    GET /api/messaging/conversations/
    Returns all conversations for the current user.
    """
    serializer_class = ConversationSerializer
    permission_classes = [IsPatientOrValidatedDoctor]

    def get_queryset(self):
        user = self.request.user
        if user.is_patient:
            return Conversation.objects.filter(patient=user).select_related('doctor', 'patient')
        elif user.is_doctor:
            return Conversation.objects.filter(doctor=user).select_related('doctor', 'patient')
        return Conversation.objects.none()

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx


@extend_schema(tags=_TAG, summary='Iniciar Conversa', description='Inicia ou recupera uma conversa com outro usuário. Informe other_user_id no body.')
class StartConversationView(APIView):
    """
    POST /api/messaging/conversations/start/
    Start or retrieve a conversation with a doctor (patient) or patient (doctor).
    Body: { "other_user_id": <id> }
    """
    permission_classes = [IsPatientOrValidatedDoctor]

    def post(self, request):
        other_user_id = request.data.get('other_user_id') or request.data.get('doctor_id')
        if not other_user_id:
            return Response({'error': 'other_user_id ou doctor_id é obrigatório.'}, status=400)

        other_user = None
        try:
            other_user = User.objects.get(pk=other_user_id)
        except User.DoesNotExist:
            # Check if other_user_id corresponds to a DoctorProfile ID
            try:
                from apps.accounts.models import DoctorProfile
                doctor_profile = DoctorProfile.objects.get(pk=other_user_id)
                other_user = doctor_profile.user
            except DoctorProfile.DoesNotExist:
                pass

        if not other_user:
            return Response({'error': 'Usuário não encontrado.'}, status=404)

        user = request.user

        if user.is_patient:
            if not other_user.is_doctor:
                return Response({'error': 'Você só pode iniciar conversas com médicos.'}, status=400)
            patient, doctor = user, other_user
        else:
            if not other_user.is_patient:
                return Response({'error': 'Você só pode iniciar conversas com pacientes.'}, status=400)
            patient, doctor = other_user, user

        conversation, created = Conversation.objects.get_or_create(
            patient=patient, doctor=doctor
        )
        return Response(
            ConversationSerializer(conversation, context={'request': request}).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


@extend_schema_view(
    get=extend_schema(tags=_TAG, summary='Listar Mensagens', description='Mensagens de uma conversa específica. Mensagens recebidas são marcadas como lidas automaticamente.'),
    post=extend_schema(tags=_TAG, summary='Enviar Mensagem', description='Envia uma nova mensagem na conversa. Use status=pending para registros offline.'),
)
class MessageListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/messaging/conversations/{id}/messages/  — list messages
    POST /api/messaging/conversations/{id}/messages/  — send a message
    """
    permission_classes = [IsPatientOrValidatedDoctor]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SendMessageSerializer
        return MessageSerializer

    def get_conversation(self):
        user = self.request.user
        conv_id = self.kwargs['pk']
        if user.is_patient:
            return Conversation.objects.get(pk=conv_id, patient=user)
        elif user.is_doctor:
            return Conversation.objects.get(pk=conv_id, doctor=user)
        raise Conversation.DoesNotExist

    def get_queryset(self):
        try:
            conversation = self.get_conversation()
            # Mark messages from the other person as read
            conversation.messages.filter(read=False).exclude(
                sender=self.request.user
            ).update(read=True)
            return conversation.messages.all()
        except Conversation.DoesNotExist:
            return Message.objects.none()

    def perform_create(self, serializer):
        try:
            conversation = self.get_conversation()
        except Conversation.DoesNotExist:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Você não tem acesso a esta conversa.')

        serializer.save(
            conversation=conversation,
            sender=self.request.user,
        )
        # Update conversation timestamp
        conversation.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            MessageSerializer(serializer.instance).data,
            status=status.HTTP_201_CREATED
        )


@extend_schema(tags=_TAG, summary='Sincronizar Mensagens Offline', description='Sincroniza em lote mensagens criadas sem conexão. Envie uma lista de objetos com conversation_id, content e sent_at.')
class SyncPendingMessagesView(APIView):
    """
    POST /api/messaging/sync/
    Sync messages that were created offline (status=pending).
    Body: list of pending messages [{ conversation_id, content, sent_at }]
    """
    permission_classes = [IsPatientOrValidatedDoctor]

    def post(self, request):
        messages_data = request.data.get('messages', [])
        synced = []
        errors = []

        user = request.user
        for msg_data in messages_data:
            try:
                conv_id = msg_data.get('conversation_id')
                if user.is_patient:
                    conversation = Conversation.objects.get(pk=conv_id, patient=user)
                else:
                    conversation = Conversation.objects.get(pk=conv_id, doctor=user)

                message = Message.objects.create(
                    conversation=conversation,
                    sender=user,
                    content=msg_data.get('content', ''),
                    status=Message.Status.SENT,
                    sent_at=msg_data.get('sent_at'),
                )
                synced.append(message.id)
                conversation.save()
            except Exception as e:
                errors.append({'data': msg_data, 'error': str(e)})

        return Response({
            'synced_count': len(synced),
            'synced_ids': synced,
            'errors': errors,
        })
