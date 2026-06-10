from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(
        label=_('Email'),
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    first_name = forms.CharField(
        label=_('Имя'),
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label=_('Фамилия'),
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        label=_('Телефон'),
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password1 = forms.CharField(
        label=_('Пароль'),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    password2 = forms.CharField(
        label=_('Подтверждение пароля'),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text=_('Введите тот же пароль, что и выше, для подтверждения.')
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('Пользователь с таким email уже существует.'))
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['email']  # Используем email как username
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data['phone']
        if commit:
            user.save()
        return user

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 
                 'delivery_region', 'delivery_city', 'delivery_street', 
                 'delivery_house', 'delivery_apartment', 'delivery_postal_code']
        labels = {
            'email': _('Email'),
            'first_name': _('Имя'),
            'last_name': _('Фамилия'),
            'phone': _('Телефон'),
            'delivery_region': _('Область/Регион'),
            'delivery_city': _('Город'),
            'delivery_street': _('Улица'),
            'delivery_house': _('Дом'),
            'delivery_apartment': _('Квартира'),
            'delivery_postal_code': _('Почтовый индекс')
        } 