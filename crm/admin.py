from django.contrib import admin
from .models import Contact, PipelineStage, Tag, Lead, LeadStage, Note, Task, Assignment

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'phone', 'email', 'created_at')
    search_fields = ('first_name', 'last_name', 'phone', 'email')

@admin.register(PipelineStage)
class PipelineStageAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order', 'is_won', 'is_lost')
    list_editable = ('order', 'is_won', 'is_lost')
    search_fields = ('name', 'slug')

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')

class NoteInline(admin.TabularInline):
    model = Note
    extra = 0

class TaskInline(admin.TabularInline):
    model = Task
    extra = 0

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'status', 'source', 'assignee', 'created_at')
    list_filter = ('status', 'source', 'assignee', 'stage')
    search_fields = ('title', 'contact__phone', 'contact__email')
    inlines = [NoteInline, TaskInline]
    actions = ['mark_contacted', 'mark_qualified', 'mark_won', 'mark_lost']

    def mark_contacted(self, request, queryset):
        queryset.update(status='contacted')
    mark_contacted.short_description = 'Отметить как: Связались'

    def mark_qualified(self, request, queryset):
        queryset.update(status='qualified')
    mark_qualified.short_description = 'Отметить как: Квалифицирован'

    def mark_won(self, request, queryset):
        queryset.update(status='won')
    mark_won.short_description = 'Отметить как: Сделка'

    def mark_lost(self, request, queryset):
        queryset.update(status='lost')
    mark_lost.short_description = 'Отметить как: Потерян'

@admin.register(LeadStage)
class LeadStageAdmin(admin.ModelAdmin):
    list_display = ('lead', 'from_stage', 'to_stage', 'changed_by', 'changed_at')
    list_filter = ('from_stage', 'to_stage')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'lead', 'assignee', 'status', 'due_at')
    list_filter = ('status', 'assignee')
    search_fields = ('title',)

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('lead', 'author', 'created_at')
    search_fields = ('text',)

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('lead', 'assignee', 'assigned_at', 'unassigned_at')
    list_filter = ('assignee',)
