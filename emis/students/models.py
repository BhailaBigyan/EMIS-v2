from django.db import models
from django.contrib.auth.hashers import make_password
from django.db.models import Q


class Students(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('graduated', 'Graduated'),
        ('suspended', 'Suspended'),
    ]

    student_id = models.AutoField(primary_key=True)
    roll_number = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=15, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M')
    address = models.TextField(blank=True)

    program = models.ForeignKey(
        'academics.Program', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='students'
    )
    batch = models.CharField(max_length=20, blank=True, help_text='e.g. 2081')
    current_semester = models.IntegerField(default=1)
    section = models.CharField(max_length=10, default='A', blank=True)

    enrollment_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    guardian_name = models.CharField(max_length=200, blank=True)
    guardian_phone = models.CharField(max_length=15, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['roll_number']
        verbose_name = 'Student'
        verbose_name_plural = 'Students'

    def __str__(self):
        return f"{self.roll_number} - {self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def set_default_password(self):
        """Set default password as emis@{roll_number}"""
        raw_password = f"emis@{self.roll_number}"
        self.password = make_password(raw_password)
        return raw_password


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('leave', 'Leave'),
    ]

    student = models.ForeignKey(
        Students, on_delete=models.CASCADE, related_name='attendance_records'
    )
    course_assignment = models.ForeignKey(
        'academics.CourseAssignment', on_delete=models.CASCADE,
        null=True, blank=True, related_name='attendance_records',
        help_text='Set when attendance is marked by a teacher for a specific class.'
    )
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    remarks = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-date']
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'course_assignment', 'date'],
                condition=Q(course_assignment__isnull=False),
                name='unique_course_attendance_per_day',
            ),
        ]
        verbose_name = 'Attendance Record'
        verbose_name_plural = 'Attendance Records'

    def __str__(self):
        return f"{self.student.roll_number} - {self.date} ({self.get_status_display()})"