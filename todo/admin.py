from django.contrib import admin
from .models import UserModel, TaskModel, TaskHistoryModel, TelegramUserModel

# Register your models here.
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'role', 'email']
    list_filter = ['role']

class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'assignee', 'status', 'priority', 'deadline']
    list_filter = ['status', 'priority', 'assignee']
    search_fields = ['title', 'desription']
    date_hierarchy = 'created_at'

class TaskHistoryAdmin(admin.ModelAdmin):
    list_display = ['task', 'changed_by', 'field_changed', 'changed_at']
    list_filter = ['changed_at', 'field_changed']
    raw_id_fields = ['task', 'changed_by']

class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'telegram_id', 'is_active']
    search_fields = ['user__username', 'tekegram_id']


    
admin.site.register(UserModel, UserAdmin)
admin.site.register(TaskModel, TaskAdmin)
admin.site.register(TaskHistoryModel, TaskHistoryAdmin)
admin.site.register(TelegramUserModel, TelegramUserAdmin)
