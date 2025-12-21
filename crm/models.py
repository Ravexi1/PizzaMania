from django.db import models
from django.contrib.auth.models import User


class Contact(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='crm_contacts')
    user_profile = models.ForeignKey('webapp.UserProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='crm_contacts')
    first_name = models.CharField(max_length=100, blank=True, default='')
    last_name = models.CharField(max_length=100, blank=True, default='')
    phone = models.CharField(max_length=32, db_index=True)
    email = models.EmailField(blank=True, null=True, db_index=True)
    street = models.CharField(max_length=200, blank=True, default='')
    entrance = models.CharField(max_length=10, blank=True, default='')
    apartment = models.CharField(max_length=10, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Контакт'
        verbose_name_plural = 'Контакты'
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        name = (self.first_name + ' ' + self.last_name).strip() or (self.user.get_username() if self.user else '')
        return name or self.phone


class PipelineStage(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    order = models.PositiveIntegerField(default=0)
    is_won = models.BooleanField(default=False)
    is_lost = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Стадия воронки'
        verbose_name_plural = 'Стадии воронки'
        ordering = ['order']

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Lead(models.Model):
    SOURCE_CHOICES = [
        ('order', 'Order'),
        ('order_cook', 'Order (Cook)'),
        ('order_courier', 'Order (Courier)'),
        ('chat', 'Chat'),
        ('review', 'Review'),
        ('manual', 'Manual'),
    ]
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('contacted', 'Связались'),
        ('qualified', 'Квалифицирован'),
        ('won', 'Завершено'),
        ('lost', 'Отменено'),
    ]

    title = models.CharField(max_length=200, blank=True, default='')
    description = models.TextField(blank=True, default='')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='leads')
    stage = models.ForeignKey(PipelineStage, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', db_index=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual', db_index=True)
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_leads')
    tags = models.ManyToManyField(Tag, blank=True, related_name='leads')

    related_order = models.ForeignKey('webapp.Order', on_delete=models.SET_NULL, null=True, blank=True)
    related_chat = models.ForeignKey('webapp.Chat', on_delete=models.SET_NULL, null=True, blank=True)
    related_review = models.ForeignKey('webapp.Review', on_delete=models.SET_NULL, null=True, blank=True)

    first_response_at = models.DateTimeField(null=True, blank=True)
    last_touch_at = models.DateTimeField(null=True, blank=True)
    is_archived = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Лид'
        verbose_name_plural = 'Лиды'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['source']),
        ]

    def __str__(self):
        return self.title or f"Лид #{self.pk}"


class LeadStage(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='stage_history')
    from_stage = models.ForeignKey(PipelineStage, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    to_stage = models.ForeignKey(PipelineStage, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.CharField(max_length=200, blank=True, default='')
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'История стадий лида'
        verbose_name_plural = 'Истории стадий лида'
        ordering = ['-changed_at']


class Note(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='notes')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Заметка'
        verbose_name_plural = 'Заметки'
        ordering = ['-created_at']


class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'В ожидании'),
        ('done', 'Выполнено'),
        ('cancelled', 'Отменено'),
    ]
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='tasks')
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='crm_tasks')
    title = models.CharField(max_length=200)
    due_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        ordering = ['status', 'due_at']

    def __str__(self):
        return self.title


class Assignment(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='assignments')
    assignee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lead_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    unassigned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Назначение'
        verbose_name_plural = 'Назначения'
        ordering = ['-assigned_at']
        constraints = [
            models.UniqueConstraint(fields=['lead', 'assignee', 'assigned_at'], name='uniq_lead_assignee_time')
        ]
