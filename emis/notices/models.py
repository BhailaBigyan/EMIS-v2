from django.db import models


class Notice(models.Model):
    CATEGORY_CHOICES = [
        ('academic', 'Academic'),
        ('exam', 'Examination'),
        ('admin', 'Administrative'),
        ('event', 'Event / Activity'),
        ('general', 'General Notice'),
    ]

    title = models.CharField(max_length=255)
    content = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    is_important = models.BooleanField(default=False)
    published_date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-published_date', '-created_at']

    def __str__(self):
        return f"[{self.get_category_display()}] {self.title}"
