from django.shortcuts import render
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .models import Book, Author, BookCopy, Genre

def index(request):
  """View function for home page of site."""
  num_books = Book.objects.all().count()
  num_copies = BookCopy.objects.all().count()
  num_genres = Genre.objects.count()

  num_books_available = BookCopy.objects.filter(status__exact='a').count()
  num_programming_books = Book.objects.all().filter(genre__name__contains="Programming").count()

  num_authors = Author.objects.count()

  num_visits = request.session.get('num_visits', 0)
  num_visits += 1
  request.session['num_visits'] = num_visits

  context = {
    'num_books': num_books,
    'num_copies': num_copies,
    'num_genres': num_genres,
    'num_books_available': num_books_available,
    'num_programming_books': num_programming_books,
    'num_authors': num_authors,
    'num_visits': num_visits
  }

  return render(request, 'index.html', context=context)

"""
BookCopy.status is a choices field, so Django automatically creates a method "get_foo_display()" for every choices filed "foo" in a model. 
"""
class BookListView(generic.ListView):
  model = Book
  context_object_name = 'book_list'
  paginate_by = 5

  """   def get_queryset(self):
    return Book.objects.filter(title__icontains='pro')[:5] """

  def get_context_data(self, **kwargs):
    context = super(BookListView, self).get_context_data(**kwargs)

    context['extra_data'] = 'Hey! extra data!'

    return context

class BookDetailView(generic.DetailView):
  model = Book

class AuthorListView(generic.ListView):
  model = Author
  context_object_name = 'author_list'
  paginate_by = 3

  def get_context_data(self, **kwargs):
    context = super(AuthorListView, self).get_context_data(**kwargs)

    written_books = 12
    context['written_books'] = written_books

    return context


class AuthorDetailView(generic.DetailView):
  model = Author

class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
  """Generic class-based view listing books on loan to current user."""
  model = BookCopy
  context_object_name = 'bookcopy_list'
  template_name = 'catalog/bookcopy_list_borrowed_user.html'
  paginate_by = 1

  def get_queryset(self):
    return (
      BookCopy.objects.filter(borrower=self.request.user)
        .filter(status__exact='o')
        .order_by('due_back')
    )

class LoanedBooksAllListView(PermissionRequiredMixin, generic.ListView):
  model = BookCopy
  context_object_name = 'bookcopy_list'
  template_name = 'catalog/bookcopy_list_borrowed_all.html'
  paginate_by = 10
  permission_required = 'catalog.can_mark_returned'

  def get_queryset(self):
    return (
      BookCopy.objects.all()
        .filter(status__exact='o')
        .order_by('due_back')
    )
