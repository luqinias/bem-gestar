from django.urls import path
from .views import (
    ConversationListView,
    StartConversationView,
    MessageListCreateView,
    SyncPendingMessagesView,
)

urlpatterns = [
    path('conversations/', ConversationListView.as_view(), name='conversations-list'),
    path('conversations/start/', StartConversationView.as_view(), name='conversation-start'),
    path('conversations/<int:pk>/messages/', MessageListCreateView.as_view(), name='messages-list'),
    path('sync/', SyncPendingMessagesView.as_view(), name='messages-sync'),
]
