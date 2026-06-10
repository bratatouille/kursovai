from django.core.management.base import BaseCommand
from django.utils import timezone
from store.models import PromoCode
from django.db.models import F

class Command(BaseCommand):
    help = 'Updates the status of promo codes based on their expiration date and usage limits.'

    def handle(self, *args, **options):
        now = timezone.now()
        
        # Deactivate expired promo codes
        expired_codes = PromoCode.objects.filter(
            status='active',
            end_date__lt=now
        )
        expired_count = expired_codes.count()
        if expired_count > 0:
            expired_codes.update(status='expired')
            self.stdout.write(self.style.SUCCESS(f'Successfully marked {expired_count} promo codes as expired.'))
        
        # Deactivate used up promo codes
        # Note: we filter on status='active' to avoid re-processing codes that are already inactive for other reasons.
        used_up_codes = PromoCode.objects.filter(
            status='active',
            usage_limit__isnull=False,
            used_count__gte=F('usage_limit')
        )
        used_up_count = used_up_codes.count()
        if used_up_count > 0:
            used_up_codes.update(status='used_up')
            self.stdout.write(self.style.SUCCESS(f'Successfully marked {used_up_count} promo codes as used up.'))
        
        if expired_count == 0 and used_up_count == 0:
             self.stdout.write(self.style.NOTICE('No promo codes needed an update.'))
        else:
            self.stdout.write(self.style.SUCCESS('Promo code status update complete.')) 