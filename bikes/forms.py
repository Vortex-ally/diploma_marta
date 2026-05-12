from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
import re

from .models import UserProfile, Review, RidePost


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False, label='Email')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Логін'
        self.fields['username'].help_text = 'Літери, цифри та @ . + - _ довжиною до 150 символів.'
        self.fields['password1'].label = 'Пароль'
        self.fields['password1'].help_text = None
        self.fields['password2'].label = 'Підтвердження пароля'
        self.fields['password2'].help_text = 'Введіть той самий пароль ще раз.'
        for field in self.fields.values():
            field.widget.attrs.update({
                'style': 'padding:10px 12px;border:1px solid #d6e0f0;border-radius:8px;background:#fff;width:100%;max-width:100%;',
            })


class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Логін')
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'style': 'padding:10px 12px;border:1px solid #d6e0f0;border-radius:8px;background:#fff;',
            })


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        labels = {
            'first_name': "Ім'я",
            'last_name': 'Прізвище',
            'email': 'Email',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make core identity fields required in profile (like checkout)
        for k in ('first_name', 'last_name', 'email'):
            if k in self.fields:
                self.fields[k].required = True
        for field in self.fields.values():
            field.widget.attrs.update({
                'style': 'padding:10px 12px;border:1px solid #d6e0f0;border-radius:8px;background:#fff;',
            })


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('photo', 'phone', 'city', 'gender', 'age', 'height_cm', 'weight_kg', 'bio')
        labels = {
            'photo': 'Фото',
            'phone': 'Телефон',
            'city': 'Місто',
            'gender': 'Стать',
            'age': 'Вік',
            'height_cm': 'Ріст (см)',
            'weight_kg': 'Вага (кг)',
            'bio': 'Про себе',
        }
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'age': forms.NumberInput(attrs={'min': 1, 'max': 120, 'inputmode': 'numeric'}),
            'height_cm': forms.NumberInput(attrs={'min': 50, 'max': 250, 'inputmode': 'numeric'}),
            'weight_kg': forms.NumberInput(attrs={'min': 20, 'max': 250, 'inputmode': 'numeric'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'style': 'padding:10px 12px;border:1px solid #d6e0f0;border-radius:8px;background:#fff;',
            })
        if 'photo' in self.fields:
            self.fields['photo'].widget = forms.ClearableFileInput()
            self.fields['photo'].widget.attrs.update({'accept': 'image/*'})

        # Phone required like checkout (masked on client, validated on server)
        if 'phone' in self.fields:
            self.fields['phone'].required = True
            self.fields['phone'].widget.attrs.update({
                'type': 'tel',
                'inputmode': 'tel',
                'autocomplete': 'tel',
                'placeholder': '+38 (0__) ___ __ __',
                'pattern': r'[0-9+() \-]{7,30}',
                'title': 'Тільки цифри (можна +, пробіли, дужки, дефіси)',
            })

        self.fields['gender'].choices = [
            ('', '---------'),
            ('female', 'Жіноча'),
            ('male', 'Чоловіча'),
            ('other', 'Інше'),
        ]
        self.fields['gender'].required = True

        for k in ('age', 'height_cm', 'weight_kg'):
            if k in self.fields:
                self.fields[k].required = True



    def clean_phone(self):
        raw = (self.cleaned_data.get('phone') or '').strip()
        if not raw:
            raise forms.ValidationError('Вкажіть номер телефону.')
        if re.search(r'[^0-9+() \-]', raw):
            raise forms.ValidationError('Тільки цифри (можна +, пробіли, дужки, дефіси).')
        digits = re.sub(r'\D', '', raw)
        if len(digits) < 10:
            raise forms.ValidationError('Номер телефону занадто короткий.')
        if len(raw) > 50:
            raise forms.ValidationError('Номер телефону занадто довгий.')
        return raw


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ('author', 'rating', 'text')
        labels = {
            'author': "Ім'я",
            'rating': 'Оцінка',
            'text': 'Відгук',
        }
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Напишіть коротко, що сподобалось/не сподобалось…'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rating'].choices = [(i, f'{i} / 5') for i in range(5, 0, -1)]
        for field in self.fields.values():
            field.widget.attrs.update({
                'style': 'padding:10px 12px;border:1px solid #d6e0f0;border-radius:8px;background:#fff;width:100%;max-width:100%;',
            })


class RidePostForm(forms.ModelForm):
    class Meta:
        model = RidePost
        fields = ('city', 'start_at', 'distance_km', 'pace', 'ride_type', 'level', 'note', 'contact_handle')
        labels = {
            'city': 'Місто',
            'start_at': 'Дата та час',
            'distance_km': 'Дистанція (км)',
            'pace': 'Темп',
            'ride_type': 'Тип катання',
            'level': 'Рівень',
            'note': 'Опис',
            'contact_handle': 'Контакт (після прийняття заявки)',
        }
        widgets = {
            'start_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'note': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'style': 'padding:10px 12px;border:1px solid #d6e0f0;border-radius:8px;background:#fff;width:100%;max-width:100%;',
            })
