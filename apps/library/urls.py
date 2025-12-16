from django.urls import path
from . import views

app_name = 'library'

urlpatterns = [
    # 基本路由
    path('', views.index, name='index'),

    # 書籍相關路由
    path('books/', views.book_list, name='book_list'),
    path('books/<int:book_id>/', views.book_detail, name='book_detail'),

    # 出版社相關路由
    path('publishers/', views.publisher_list, name='publisher_list'),
    path('publishers/<int:publisher_id>/', views.publisher_detail, name='publisher_detail'),
    path('publishers/<int:publisher_id>/books/', views.publisher_books, name='publisher_books'),
]
# apps/library/urls.py
from django.urls import path
from . import views

app_name = 'library'

urlpatterns = [
    path('books/', views.BookListView.as_view(), name='book_list'),
    path('books/<int:book_id>/', views.BookDetailView.as_view(), name='book_detail'),
    path('books/create/', views.BookCreateView.as_view(), name='book_create'),
    path('books/<int:book_id>/edit/', views.BookEditView.as_view(), name='book_edit'),
    path('books/<int:book_id>/delete/', views.BookDeleteView.as_view(), name='book_delete'),
    path('books/', views.BookListView.as_view(), name='book_list'),
]
