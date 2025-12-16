from django.db import models


class Publisher(models.Model):
    """出版社"""
    name = models.CharField(max_length=100, verbose_name='出版社名稱')
    city = models.CharField(max_length=50, verbose_name='出版社所在城市')

    class Meta:
        verbose_name = '出版社'
        verbose_name_plural = '出版社'

    def __str__(self):
        return self.name
