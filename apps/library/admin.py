from django.contrib import admin
from .models import Book, BookDetail, Publisher, Author  # 加入 Author


# 註冊 Publisher
@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'city']
    search_fields = ['name', 'city']


# 註冊 Author
@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'nationality', 'birth_date']
    search_fields = ['name']
    list_filter = ['nationality']


# 註冊 Book
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'price', 'stock', 'publisher']
    list_filter = ['publisher', 'authors']
    search_fields = ['title']
    filter_horizontal = ['authors']  # 在 admin 中使用水平篩選器來選擇作者


# 註冊 BookDetail
@admin.register(BookDetail)
class BookDetailAdmin(admin.ModelAdmin):
    list_display = ['id', 'book', 'isbn', 'publisher', 'publish_date', 'pages']
    search_fields = ['isbn', 'book__title']
