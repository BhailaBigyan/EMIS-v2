from django.db import models
import uuid


class FeeStructure(models.Model):
    name = models.CharField(max_length=200)
    program = models.ForeignKey(
        'academics.Program', on_delete=models.CASCADE, related_name='fee_structures'
    )
    semester = models.IntegerField(default=1)
    academic_year = models.ForeignKey(
        'academics.AcademicYear', on_delete=models.CASCADE
    )
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    lab_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    library_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    exam_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_fee(self):
        return (self.tuition_fee + self.lab_fee + self.library_fee +
                self.exam_fee + self.other_fee)

    class Meta:
        ordering = ['program', 'semester']

    def __str__(self):
        return f"{self.name} - {self.program.code} (Sem {self.semester})"


class FeePayment(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('online', 'Online Payment (eSewa/Khalti)'),
        ('cheque', 'Cheque'),
    ]

    STATUS_CHOICES = [
        ('paid', 'Fully Paid'),
        ('partial', 'Partially Paid'),
        ('pending', 'Pending'),
        ('refunded', 'Refunded'),
    ]

    student = models.ForeignKey(
        'students.Students', on_delete=models.CASCADE,
        related_name='fee_payments'
    )
    fee_structure = models.ForeignKey(
        FeeStructure, on_delete=models.CASCADE, related_name='payments'
    )
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHODS, default='cash'
    )
    transaction_id = models.CharField(max_length=100, blank=True)
    receipt_number = models.CharField(max_length=50, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='paid')
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date']

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = f"RCP-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.receipt_number} - {self.student.roll_number} ({self.amount_paid})"


class StudentFeeAccount(models.Model):
    """Tracks per-student fee balance for a specific fee structure."""
    student = models.ForeignKey(
        'students.Students', on_delete=models.CASCADE,
        related_name='fee_accounts'
    )
    fee_structure = models.ForeignKey(
        FeeStructure, on_delete=models.CASCADE, related_name='student_accounts'
    )
    total_due = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'fee_structure')
        ordering = ['student__roll_number']

    @property
    def balance(self):
        return self.total_due - self.total_paid

    @property
    def is_fully_paid(self):
        return self.total_paid >= self.total_due

    def __str__(self):
        return f"{self.student.roll_number} - {self.fee_structure.name} (Balance: {self.balance})"


class Salary(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
    ]

    teacher = models.ForeignKey(
        'teachers.Teacher', on_delete=models.CASCADE,
        related_name='salaries'
    )
    month = models.CharField(max_length=50)  # e.g. "August 2025"
    base_salary = models.DecimalField(max_digits=10, decimal_places=2)
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_date = models.DateField(null=True, blank=True)
    payment_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def net_salary(self):
        return (self.base_salary + self.allowances) - self.deductions

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Salary: {self.teacher.full_name} ({self.month}) - {self.payment_status}"
