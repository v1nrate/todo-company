from django import forms
from .models import TaskFile, UserModel, TaskModel
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from django.forms import inlineformset_factory

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

class CustomAuthenticationForm(AuthenticationForm):
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password
            )
            if self.user_cache is None:
                raise forms.ValidationError(
                    "Неверное имя пользователя или пароль.",
                    code='invalid_login'
                )
            # Проверка: подтверждён ли email?
            if not self.user_cache.is_active:
                raise forms.ValidationError(
                    "Ваш email не подтверждён. Проверьте почту и перейдите по ссылке активации.",
                    code='inactive'
                )
        return self.cleaned_data
        
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
        fields = ['title', 'description', 'assignee', 'deadline', 'priority', 'status']
