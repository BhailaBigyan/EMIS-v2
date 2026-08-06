from django.db import models
from django.conf import settings


class Exam(models.Model):
    EXAM_TYPES = [
        ('first assessment', 'First Assessment'),
        ('second assessment', 'Second Assessment'),
        ('practical', 'Practical Exam'),
    ]

    name = models.CharField(max_length=200)
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES, default='final')
    semester = models.ForeignKey('academics.Semester', on_delete=models.CASCADE, related_name='exams')
    start_date = models.DateField()
    end_date = models.DateField()
    total_marks = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    pass_marks = models.DecimalField(max_digits=5, decimal_places=2, default=40.00)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.name} ({self.semester.name})"


class ExamSchedule(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='schedules')
    course = models.ForeignKey('academics.Course', on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50)
    # invigilator = models.ForeignKey(
    #     settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
    #     limit_choices_to={'role': 'teacher'}
    # )

    class Meta:
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.exam.name} - {self.course.code} on {self.date}"


class Grade(models.Model):
    # student = models.ForeignKey(
    #     'student_management.StudentProfile', on_delete=models.CASCADE,
    #     related_name='grades'
    # )
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='grades')
    course = models.ForeignKey('academics.Course', on_delete=models.CASCADE)
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    grade_letter = models.CharField(max_length=5, blank=True)
    remarks = models.CharField(max_length=255, blank=True)
    graded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # class Meta:
        # unique_together = ('student', 'exam', 'course')
        # ordering = ['student__roll_number']

    def save(self, *args, **kwargs):
        # Auto-compute grade letter if possible
        if self.exam.total_marks > 0:
            percentage = (float(self.marks_obtained) / float(self.exam.total_marks)) * 100
            if percentage >= 90: self.grade_letter = 'A+'
            elif percentage >= 80: self.grade_letter = 'A'
            elif percentage >= 70: self.grade_letter = 'B'
            elif percentage >= 60: self.grade_letter = 'C'
            elif percentage >= 50: self.grade_letter = 'D'
            else: self.grade_letter = 'F'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.roll_number} - {self.course.code}: {self.marks_obtained}"


class Result(models.Model):
    STATUS_CHOICES = [
        ('pass', 'Passed'),
        ('fail', 'Failed'),
        ('withheld', 'Withheld'),
    ]

    # student = models.ForeignKey(
    #     'student_management.StudentProfile', on_delete=models.CASCADE,
    #     related_name='results'
    # )
    semester = models.ForeignKey('academics.Semester', on_delete=models.CASCADE)
    total_marks = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    obtained_marks = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    gpa = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    rank = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pass')
    published = models.BooleanField(default=False)
    published_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        # unique_together = ('student', 'semester')
        ordering = ['-semester', 'rank']

    def __str__(self):
        return f"Result: {self.student.roll_number} - {self.semester.name}"
