from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views import View

from .models import Book, BookDetail, Publisher


class HelloWorldView(View):
    def get(self, request):
        return HttpResponse("Hello, World!")


def index(request):
    """Simple landing page for the library app."""
    book_count = Book.objects.count()
    publisher_count = Publisher.objects.count()
    return HttpResponse(
        f"Library index — books: {book_count}, publishers: {publisher_count}"
    )


def book_list(request):
    titles = ", ".join(Book.objects.values_list("title", flat=True))
    if not titles:
        titles = "No books available."
    return HttpResponse(f"Books: {titles}")


def book_detail(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    detail = getattr(book, "detail", None)
    description = detail.description if detail else "No description."
    return HttpResponse(
        f"{book.title} — price: {book.price}, stock: {book.stock}, description: {description}"
    )


def publisher_list(request):
    names = ", ".join(Publisher.objects.values_list("name", flat=True))
    if not names:
        names = "No publishers available."
    return HttpResponse(f"Publishers: {names}")


def publisher_detail(request, publisher_id):
    publisher = get_object_or_404(Publisher, pk=publisher_id)
    return HttpResponse(f"{publisher.name} — {publisher.address if hasattr(publisher, 'address') else 'No address provided.'}")


def publisher_books(request, publisher_id):
    publisher = get_object_or_404(Publisher, pk=publisher_id)
    titles = ", ".join(publisher.books.values_list("title", flat=True))
    if not titles:
        titles = "No books for this publisher."
    return HttpResponse(f"{publisher.name} books: {titles}")
from django.shortcuts import render
from django.views import View
from .models import Book

class BookListView(View):
    """書籍列表頁"""

    def get(self, request):
        books = Book.objects.select_related('publisher').all()

        context = {
            'books': books,
            'total_count': books.count(),
        }

        return render(request, 'library/book_list.html', context)