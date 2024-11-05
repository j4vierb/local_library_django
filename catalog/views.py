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
  template_name = 'book_list.html'
  paginate_by = 5

  """   def get_queryset(self):
    return Book.objects.filter(title__icontains='pro')[:5] """

  def get_context_data(self, **kwargs):
    context = super(BookListView, self).get_context_data(**kwargs)

    context['extra_data'] = 'Hey! extra data!'

    return context

class BookDetailView(generic.DetailView):
  model = Book
  template_name = 'book_detail.html'

class AuthorListView(generic.ListView):
  model = Author
  context_object_name = 'author_list'
  template_name = 'author_list.html'
  paginate_by = 3

  def get_context_data(self, **kwargs):
    context = super(AuthorListView, self).get_context_data(**kwargs)

    written_books = 12
    context['written_books'] = written_books

    return context


class AuthorDetailView(generic.DetailView):
  model = Author
  template_name = 'author_detail.html'

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

# Forms in Django

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from catalog.forms import RenewBookForm
from datetime import date, timedelta

@login_required
@permission_required('catalog.can_mark_returned', raise_exception=True)
def renew_book_librarian(request, pk):
  book_instance = get_object_or_404(BookCopy, pk=pk)

  if request.method == 'POST':
    form = RenewBookForm(request.POST)

    if form.is_valid():
      # data binding
      book_instance.due_back = form.cleaned_data['renewal_date']
      book_instance.save()

      return HttpResponseRedirect(reverse('all-borrowed'))
  else:
    proposed_renewal_date = date.today() + timedelta(weeks=3)
    form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})

  context = {
    'form': form,
    'book_instance': book_instance
  }

  return render(request, 'catalog/book_renew_librarian.html', context)

# Generic editing views
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Author

class AuthorCreate(PermissionRequiredMixin, CreateView):
  model = Author
  fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
  initial = {'date_of_death': '11/11/2023'}
  permission_required = 'catalog.add_author'
  template_name = 'author_form.html'

class AuthorUpdate(PermissionRequiredMixin, UpdateView):
  model = Author
  fields = '__all__'
  permission_required = 'catalog.change_author'
  template_name = 'author_form.html'

class AuthorDelete(PermissionRequiredMixin, DeleteView):
  model = Author
  context_object_name = 'author'
  success_url = reverse_lazy('authors')
  permission_required = 'catalog.delete_author'
  template_name = 'author_confirm_delete.html'

  def form_valid(self, form):
    try:
      self.object.delete()
      return HttpResponseRedirect(self.success_url)
    except Exception as e:
      return HttpResponseRedirect(
        reverse('author-delete', kwargs={'pk': self.object.pk})
      )

# Book views
class BookCreate(PermissionRequiredMixin, CreateView):
  model = Book
  fields = '__all__'
  template_name = 'book_form.html'
  permission_required = 'catalog.add_book'

class BookUpdate(PermissionRequiredMixin, UpdateView):
  model = Book
  fields = '__all__'
  template_name = 'book_form.html'
  permission_required = 'catalog.change_book'

class BookDelete(PermissionRequiredMixin, DeleteView):
  model = Book
  success_url = reverse_lazy('books')
  permission_required = 'catalog.delete_book'
  template_name = 'book_confirm_delete.html'
  context_object_name = 'book'

  def form_valid(self, form):
    try:
      self.object.delete()
      return HttpResponseRedirect(self.success_url)
    except Exception as e:
      return HttpResponseRedirect(
        reverse('author-delete', kwargs={'pk': self.object.pk})
      )
