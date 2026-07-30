from django.urls import path
from .views import (
    ContentCategoryListView,
    EducationalContentListView,
    EducationalContentDetailView,
    EducationalContentBySlugView,
    HomeRecommendationsView,
)

urlpatterns = [
    path('categories/', ContentCategoryListView.as_view(), name='content-categories'),
    path('contents/', EducationalContentListView.as_view(), name='education-contents-list'),
    # Specific named routes BEFORE the generic <int:pk> route
    path('contents/home-recommendations/', HomeRecommendationsView.as_view(), name='education-home-recs'),
    path('contents/slug/<slug:slug>/', EducationalContentBySlugView.as_view(), name='education-content-by-slug'),
    path('contents/<int:pk>/', EducationalContentDetailView.as_view(), name='education-content-detail'),
]
