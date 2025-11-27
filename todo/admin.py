from django.contrib import admin
from .models import UserModel, TaskModel, TelegramUserModel

# Register your models here.
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'role', 'email']
    list_filter = ['role']

class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'assignee', 'status', 'priority', 'deadline']
    list_filter = ['status', 'priority', 'assignee']
    search_fields = ['title', 'description']
    date_hierarchy = 'created_at'

class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'telegram_id', 'is_active']
    search_fields = ['user__username', 'telegram_id']


    
admin.site.register(UserModel, UserAdmin)
admin.site.register(TaskModel, TaskAdmin)
admin.site.register(TelegramUserModel, TelegramUserAdmin)
