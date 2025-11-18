from django import forms
from .models import UserModel, TaskModel
from django.contrib.auth.forms import UserCreationForm


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")

    class Meta:
        model = UserModel
        fields = ("username", "email", "first_name", "last_name", "role", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.is_active = False  # ← не активен до подтверждения email
        if commit:
            user.save()
        return user
        
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
