from django.db import models
from django.contrib.auth.hashers import make_password


class Teacher(models.Model):
    DESIGNATION_CHOICES = [
        ('professor', 'Professor'),
        ('associate_professor', 'Associate Professor'),
        ('assistant_professor', 'Assistant Professor'),
        ('lecturer', 'Lecturer'),
        ('teaching_assistant', 'Teaching Assistant'),
    ]

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    employee_id = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128, blank=True, help_text='Hashed login password for the teacher portal')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=15, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M')
    department = models.ForeignKey(
        'academics.Department', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='teachers'
    )
    designation = models.CharField(
        max_length=30, choices=DESIGNATION_CHOICES, default='lecturer'
    )
    qualification = models.CharField(max_length=200, blank=True)
    specialization = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.employee_id} - {self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def set_default_password(self):
        """Set default password as tch@{employee_id}"""
        raw_password = f"tch@{self.employee_id}"
        self.password = make_password(raw_password)
        return raw_password

    @property
    def has_portal_access(self):
        return self.is_active and bool(self.password)


class LeaveRequest(models.Model):
    LEAVE_TYPES = [
        ('casual', 'Casual Leave'),
        ('sick', 'Sick Leave'),
        ('annual', 'Annual Leave'),
        ('unpaid', 'Unpaid Leave'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    teacher = models.ForeignKey(
        Teacher, on_delete=models.CASCADE, related_name='leave_requests'
    )
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES, default='casual')
    from_date = models.DateField()
    to_date = models.DateField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_remarks = models.CharField(max_length=255, blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.teacher.employee_id} - {self.leave_type} ({self.from_date} to {self.to_date})"

    @property
    def days(self):
        return (self.to_date - self.from_date).days + 1
