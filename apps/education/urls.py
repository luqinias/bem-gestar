from django.urls import path
from .views import (
    ContentCategoryListView,
    EducationalContentListView,
    EducationalContentDetailView,
    EducationalContentBySlugView,
)

urlpatterns = [
    path('categories/', ContentCategoryListView.as_view(), name='content-categories'),
    path('contents/', EducationalContentListView.as_view(), name='education-contents-list'),
    path('contents/<int:pk>/', EducationalContentDetailView.as_view(), name='education-content-detail'),
    path('contents/slug/<slug:slug>/', EducationalContentBySlugView.as_view(), name='education-content-by-slug'),
]
