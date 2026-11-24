from django.urls import path

from .views import ArticleDetailView, ArticleListView

urlpatterns = [
    path("", ArticleListView.as_view(), name="knowledge_list"),
    path("<int:pk>/", ArticleDetailView.as_view(), name="knowledge_detail"),
]
