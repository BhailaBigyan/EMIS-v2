from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    head = models.ForeignKey(
        'teachers.Teacher', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='headed_departments'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class Program(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name='programs'
    )
    duration_years = models.IntegerField(default=4)
    total_semesters = models.IntegerField(default=8)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class Course(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    program = models.ForeignKey(
        Program, on_delete=models.CASCADE, related_name='courses'
    )
    credit_hours = models.IntegerField(default=3)
    description = models.TextField(blank=True)
    semester = models.IntegerField(default=1)
    is_elective = models.BooleanField(default=False)

    class Meta:
        ordering = ['semester', 'code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class AcademicYear(models.Model):
    name = models.CharField(max_length=50, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_current:
            AcademicYear.objects.filter(is_current=True).update(is_current=False)
        super().save(*args, **kwargs)


class Semester(models.Model):
    academic_year = models.ForeignKey(
        AcademicYear, on_delete=models.CASCADE, related_name='semesters'
    )
    name = models.CharField(max_length=50)
    number = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ['-academic_year', 'number']
        unique_together = ('academic_year', 'number')

    def __str__(self):
        return f"{self.name} ({self.academic_year.name})"

    def save(self, *args, **kwargs):
        if self.is_current:
            Semester.objects.filter(is_current=True).update(is_current=False)
        super().save(*args, **kwargs)


class CourseAssignment(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='assignments'
    )
    teacher = models.ForeignKey(
        'teachers.Teacher', on_delete=models.CASCADE,
        related_name='course_assignments'
    )
    semester = models.ForeignKey(
        Semester, on_delete=models.CASCADE, related_name='assignments'
    )
    section = models.CharField(max_length=10, default='A')
    max_students = models.IntegerField(default=60)

    class Meta:
        unique_together = ('course', 'semester', 'section')
        ordering = ['course__code']

    def __str__(self):
        return f"{self.course.code} - {self.teacher.full_name} (Sec {self.section})"


class Timetable(models.Model):
    DAY_CHOICES = [
        ('SUN', 'Sunday'), ('MON', 'Monday'), ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'), ('THU', 'Thursday'), ('FRI', 'Friday'),
    ]
    course_assignment = models.ForeignKey(
        CourseAssignment, on_delete=models.CASCADE, related_name='timetable_slots'
    )
    day_of_week = models.CharField(max_length=3, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50)

    class Meta:
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.course_assignment.course.code} - {self.get_day_of_week_display()} {self.start_time}"


class Batch(models.Model):
    name = models.CharField(max_length=50, unique=True)
    program = models.ForeignKey(
        Program, on_delete=models.CASCADE, related_name='batches', null=True, blank=True
    )
    start_year = models.IntegerField(default=2024)
    end_year = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-name']

    def __str__(self):
        if self.program:
            return f"{self.name} ({self.program.code})"
        return self.name

