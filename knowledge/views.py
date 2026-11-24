from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.generic import DetailView, ListView

from .models import Article


class ArticleListView(LoginRequiredMixin, ListView):
    model = Article
    template_name = "knowledge/article_list.html"
    context_object_name = "articles"
    paginate_by = 9

    def get_queryset(self):
        articles = Article.objects.order_by("title")
        query = self.request.GET.get("q", "").strip()[:100]
        category = self.request.GET.get("category", "").strip()[:20]
        if query:
            articles = articles.filter(
                Q(title__icontains=query)
                | Q(symptoms__icontains=query)
                | Q(solution__icontains=query)
            )
        if category:
            articles = articles.filter(category=category)
        return articles

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")[:100]
        context["selected_category"] = self.request.GET.get("category", "")[:20]
        context["categories"] = (
            Article.objects.exclude(category="")
            .order_by("category")
            .values_list("category", flat=True)
            .distinct()
        )
        return context


class ArticleDetailView(LoginRequiredMixin, DetailView):
    model = Article
    template_name = "knowledge/article_detail.html"
    context_object_name = "article"
