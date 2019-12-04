from django.core.management import BaseCommand

from currencies.models import Currency


class Command(BaseCommand):
    help = 'Load from API and save to DB currencies data (code, name)'

    def handle(self, *args, **options):
        data = Currency.get_currencies_from_api()
        Currency.save_currencies_from_api(data)
