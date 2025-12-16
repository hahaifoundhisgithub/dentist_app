from django.db import models
from .publisher import Publisher
from .author import Author  # 匯入 Author


class Book(models.Model):
    """書籍基本資訊"""
    title = models.CharField(max_length=100, verbose_name='書名')
    price = models.IntegerField(verbose_name='價格')
    stock = models.IntegerField(default=0, verbose_name='庫存')

    # ForeignKey 建立一對多關聯
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.CASCADE,
        related_name='books',
        verbose_name='出版社',
        null=True,
        blank=True
    )

    # ManyToManyField 建立多對多關聯
    authors = models.ManyToManyField(
        Author,
        related_name='books',
        verbose_name='作者'
    )

    class Meta:
        verbose_name = '書籍'
        verbose_name_plural = '書籍'

    def __str__(self):
        return self.title
