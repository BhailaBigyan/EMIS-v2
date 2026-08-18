from django.db import models
from django.contrib.auth.hashers import make_password
from datetime import timedelta


class Librarian(models.Model):
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)
    full_name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=15, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['full_name']

    def __str__(self):
        return f"{self.username} - {self.full_name}"

    def set_default_password(self):
        raw_password = f"library@{self.username}"
        self.password = make_password(raw_password)
        return raw_password


class BookCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Book Categories'

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=300)
    author = models.CharField(max_length=200)
    isbn = models.CharField(max_length=30, blank=True, unique=True)
    category = models.ForeignKey(
        BookCategory, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='books'
    )
    publisher = models.CharField(max_length=200, blank=True)
    published_year = models.PositiveIntegerField(null=True, blank=True)
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)
    rack_location = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return f"{self.title} - {self.author}"

    @property
    def is_available(self):
        return self.available_copies > 0


class Borrowing(models.Model):
    STATUS_CHOICES = [
        ('borrowed', 'Borrowed'),
        ('returned', 'Returned'),
    ]

    LOAN_PERIOD_DAYS = 14
    FINE_PER_DAY = 5

    student = models.ForeignKey(
        'students.Students', on_delete=models.CASCADE,
        related_name='borrowings'
    )
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name='borrowings'
    )
    issued_by = models.ForeignKey(
        Librarian, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='issued_loans'
    )
    borrowed_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    return_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='borrowed')
    fine_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-borrowed_date']

    def save(self, *args, **kwargs):
        if not self.due_date:
            from django.utils import timezone
            base_date = self.borrowed_date or timezone.localdate()
            self.due_date = base_date + timedelta(days=self.LOAN_PERIOD_DAYS)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.roll_number} - {self.book.title} ({self.status})"

    @property
    def is_overdue(self):
        if self.status != 'borrowed':
            return False
        from datetime import date
        if self.due_date:
            return date.today() > self.due_date
        return False

    @property
    def overdue_days(self):
        if not self.is_overdue:
            return 0
        from datetime import date
        return (date.today() - self.due_date).days

    def calculate_fine(self):
        if self.is_overdue:
            return self.overdue_days * self.FINE_PER_DAY
        return 0

    def return_book(self):
        from datetime import date
        self.return_date = date.today()
        self.status = 'returned'
        self.fine_amount = self.calculate_fine()
        self.book.available_copies += 1
        self.book.save(update_fields=['available_copies'])
        self.save()
        return self.fine_amount