from django.db import models
from . import Book


class BookDetail(models.Model):
    """書籍詳細資訊（將不常用的資訊分離到另一個表格）"""
    # OneToOneField 建立一對一關聯
    book = models.OneToOneField(
        Book, 
        on_delete=models.CASCADE,
        related_name='detail',
        verbose_name='書籍'
    )
    isbn = models.CharField(max_length=13, unique=True, verbose_name='ISBN')
    publisher = models.CharField(max_length=100, verbose_name='出版社')
    publish_date = models.DateField(verbose_name='出版日期')
    pages = models.IntegerField(verbose_name='頁數')
    description = models.TextField(blank=True, verbose_name='內容簡介')
    cover_image = models.ImageField(upload_to='book_covers/', null=True, blank=True, verbose_name='封面圖片')

    class Meta:
        verbose_name = '書籍詳細資料'
        verbose_name_plural = '書籍詳細資料'

    def __str__(self):
        return f"{self.book.title} 的詳細資料"
