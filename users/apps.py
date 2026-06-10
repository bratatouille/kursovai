from django.apps import AppConfig
from django.db.models.signals import post_migrate

def create_superuser(sender, **kwargs):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    admin_email = 'admin@admin.com'
    admin_password = 'admin'
    
    if not User.objects.filter(email=admin_email).exists():
        User.objects.create_superuser(
            email=admin_email,
            password=admin_password,
            first_name='Admin',
            last_name='Adminovich',
            phone='+1234567890'  # Обязательное поле
        )
        print('Superuser created')
    else:
        print('Superuser already exists')


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'Пользователи'

    def ready(self):
        post_migrate.connect(create_superuser, sender=self)