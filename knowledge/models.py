from django.db import models


class Article(models.Model):
    title = models.CharField("Título", max_length=150)
    symptoms = models.TextField("Sintomas / Quando usar")
    solution = models.TextField("Solução passo a passo")
    category = models.CharField(max_length=20, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title