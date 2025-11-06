from django import forms
from .models import UserModel, TaskModel


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    class Meta:
        model = UserModel
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'password']
        
class TaskForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Настраиваем виджет для поля deadline
        self.fields['deadline'].widget = forms.DateTimeInput(
            attrs={
                'type': 'datetime-local',  # ← HTML5-виджет с календарём и временем
                'required': True,
            }
        )

    class Meta:
        model = TaskModel
        fields = ['title', 'description', 'assignee', 'created_by', 'deadline', 'priority', 'status']
