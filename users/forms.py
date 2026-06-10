from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from store.models import Product, Category

User = get_user_model()

class UserRegisterForm(UserCreationForm):
    ACCOUNT_TYPE_CHOICES = (
        ('buyer', _('Покупатель')),
        ('seller', _('Продавец')),
    )

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
    account_type = forms.ChoiceField(
        label=_('Тип аккаунта'),
        choices=ACCOUNT_TYPE_CHOICES,
        initial='buyer',
        widget=forms.RadioSelect
    )
    seller_name = forms.CharField(
        label=_('Название магазина'),
        required=False,
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
        fields = ('email', 'first_name', 'last_name', 'phone', 'account_type', 'seller_name', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('Пользователь с таким email уже существует.'))
        return email

    def clean(self):
        cleaned_data = super().clean()
        account_type = cleaned_data.get('account_type')
        seller_name = cleaned_data.get('seller_name', '').strip()
        if account_type == 'seller' and not seller_name:
            self.add_error('seller_name', _('Укажите название магазина для продавца.'))
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data['phone']
        user.is_seller = self.cleaned_data.get('account_type') == 'seller'
        user.seller_name = self.cleaned_data.get('seller_name', '').strip() if user.is_seller else ''
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


class BecomeSellerForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['seller_name']
        labels = {
            'seller_name': _('Название магазина'),
        }
        widgets = {
            'seller_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_seller_name(self):
        seller_name = self.cleaned_data.get('seller_name', '').strip()
        if not seller_name:
            raise forms.ValidationError(_('Название магазина обязательно.'))
        return seller_name


class SellerProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'category',
            'name',
            'price',
            'discount',
            'stock',
            'min_stock',
            'is_popular',
            'description',
            'image',
        ]
        labels = {
            'category': _('Категория'),
            'name': _('Название'),
            'price': _('Цена'),
            'discount': _('Скидка (%)'),
            'stock': _('Количество на складе'),
            'min_stock': _('Минимальный остаток'),
            'is_popular': _('Популярный товар'),
            'description': _('Описание'),
            'image': _('Главное фото'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.select_related('product_line').order_by(
            'product_line__name', 'name'
        )
        base_cls = 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-[#1E242E] dark:text-white'
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'h-4 w-4'})
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'block w-full text-sm text-gray-700 dark:text-gray-300'})
            else:
                field.widget.attrs.update({'class': base_cls})
        self.fields['description'].widget = forms.Textarea(attrs={
            'class': base_cls,
            'rows': 5,
        })