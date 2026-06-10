from django.core.management.base import BaseCommand

from store.search_engine import rebuild_index


class Command(BaseCommand):
    help = "Rebuild Whoosh product search index"

    def handle(self, *args, **options):
        count = rebuild_index()
        self.stdout.write(self.style.SUCCESS(f"Indexed {count} products"))
