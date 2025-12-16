from django.db import models


class Author(models.Model):
    """作者"""
    name = models.CharField(max_length=100, verbose_name='姓名')
    bio = models.TextField(blank=True, verbose_name='簡介')
    birth_date = models.DateField(null=True, blank=True, verbose_name='出生日期')
    nationality = models.CharField(max_length=50, blank=True, verbose_name='國籍')

    class Meta:
        verbose_name = '作者'
        verbose_name_plural = '作者'

    def __str__(self):
        return self.name
