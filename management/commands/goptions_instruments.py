from django.core.management.base import BaseCommand

from trade.brokers.goptions import GOptions


class Command(BaseCommand):
    help = 'Update instruments'

#    @single_access
    def handle(self, *args, **options):
        g = GOptions()
        instruments_count = g.update_instruments()
        print 'GOptions instruments has been updated:', instruments_count
