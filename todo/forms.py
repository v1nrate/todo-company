from django import forms
from .models import TaskFile, UserModel, TaskModel
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, get_user_model
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError

User = get_user_model()

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
    # Кастомные сообщения об ошибках
    error_messages = {
        'invalid_login': (
            "Неверный логин или пароль. Поля чувствительны к регистру."
        ),
        'inactive': ("Ваш аккаунт не активирован. Проверьте почту."),
    }

    def clean_username(self):
        """Преобразует email в username, если введён email."""
        username = self.cleaned_data.get('username')
        if '@' in username:
            try:
                user = User.objects.get(email__iexact=username)
                return user.username
            except User.DoesNotExist:
                # Оставляем как есть — AuthenticationForm сам выдаст ошибку
                pass
        return username

    def confirm_login_allowed(self, user):
        """Дополнительная проверка при успешной аутентификации."""
        if not user.is_active:
            raise ValidationError(
                self.error_messages['inactive'],
                code='inactive',
            )

class TaskForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Настройка виджета для deadline
        self.fields['deadline'].widget = forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'required': True}
        )
        
        # Блокируем deadline при редактировании
        if self.instance and self.instance.pk:
            self.fields['deadline'].disabled = True
        
        # Фильтруем choices для status — оставляем только 'new' и 'in_progress'
        self.fields['status'].choices = [
            (choice, label) for choice, label in TaskModel.STATUS_CHOICES 
            if choice in ['new', 'in_progress']
        ]

    class Meta:
        model = TaskModel
        fields = ['title', 'description', 'assignee', 'deadline', 'priority', 'status']
