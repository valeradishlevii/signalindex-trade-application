from django.core.management.base import BaseCommand

from trade.tasks import update_trades

class Command(BaseCommand):
    help = 'Update instruments'

    def handle(self, *args, **options):
        update_trades()
