import time

import requests
from django.db import models, connection, transaction
from rest_framework import status
from rest_framework.exceptions import ValidationError

from simple_djangorest.settings import logger, BASE_CURRENCY_CODE, EXCHANGERATES_API_MAX_RETRIES, \
    EXCHANGERATES_API_LATEST_URL, EXCHANGERATES_API_RETRY_PAUSE, EXCHANGERATES_API_CURRENCIES_URL, ACTIVE_CURRENCIES


class Currency(models.Model):
    code = models.CharField(verbose_name='3 letters code', max_length=3, db_index=True)
    name = models.CharField(verbose_name='currency full name', max_length=128)
    alias = models.CharField(verbose_name='currency customer alias', max_length=128)

    def __str__(self):
        return f'{self.code}'

    @classmethod
    def get_currencies_from_api(cls):
        r = requests.get(EXCHANGERATES_API_CURRENCIES_URL, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return [item for item in data.items() if item[1] in ACTIVE_CURRENCIES.keys()]
        else:
            logger.error(f'openexchangerates API access error: {r.status_code}')

    @classmethod
    def save_currencies_from_api(cls, data):
        for code, name in data:
            if not Currency.objects.filter(code=code).exists():
                try:
                    currency_obj = Currency.objects.create(code=code, name=name, alias=ACTIVE_CURRENCIES[name])
                    logger.debug(f'created {currency_obj}')
                except Exception as e:
                    logger.error(f'{code}: {name} not created {e}')


class CurrencyRate(models.Model):
    currency = models.ForeignKey(Currency, verbose_name='currency', on_delete=models.CASCADE)
    timestamp = models.PositiveIntegerField(verbose_name='updated TS', db_index=True)
    rate = models.FloatField(verbose_name='rate to USD')

    class Meta:
        ordering = ['currency', '-timestamp']

    def __str__(self):
        return f'{self.currency.code}: {self.rate}'

    @classmethod
    def get_rates_from_api(cls):
        """
        Load currency rates from API.

        :return: dict with API data
        """
        attempt_num = 0
        while attempt_num < EXCHANGERATES_API_MAX_RETRIES:
            try:
                r = requests.get(EXCHANGERATES_API_LATEST_URL, timeout=10)
                if r.status_code == 200:
                    return r.json()
                else:
                    attempt_num += 1
                    logger.warning(
                        f'attempt: {attempt_num}, '
                        f'URL: {EXCHANGERATES_API_LATEST_URL}, '
                        f'response status: {r.status_code}'
                    )
                    time.sleep(EXCHANGERATES_API_RETRY_PAUSE)
            except Exception as e:
                logger.error(f'{e}')

    @classmethod
    def save_rates_from_api(cls, data):
        """
        Save currency rates from dict to DB.

        :param data: dict with API data
        :return: True if success else False
        """
        try:
            timestamp = data.get('timestamp', None)
            if CurrencyRate.objects.filter(timestamp=timestamp).exists():
                logger.warning(f'rate for {timestamp} already exists')
                return False
            base = data.get('base', None)
            rates = data.get('rates', None)
            if rates and timestamp and base == BASE_CURRENCY_CODE:
                with transaction.atomic():
                    for currency in Currency.objects.exclude(code=BASE_CURRENCY_CODE).only('code'):
                        if currency.code in rates.keys():
                            currency_rate_obj = cls.objects.create(
                                currency=currency,
                                timestamp=int(timestamp),
                                rate=float(rates[currency.code]))
                            logger.debug(f'{currency_rate_obj}')
                        else:
                            logger.error(f'no currency rate {currency.code}')
                            return False
                    return True
        except Exception as e:
            logger.error(f'{e}')

    @staticmethod
    def get_pair_data(source, target):
        """
        Get source and target currency rates and its timestamp from DB.

        :param source: currency 3 letters code
        :param target: currency 3 letters code
        :return: dict with keys: <source>, <target>, 'timestamp'
        """
        pair = [source, target]
        currencies = {
            source: 1,
            target: 1
        }

        # check BASE_CURRENCY_CODE in pair
        if BASE_CURRENCY_CODE in pair:
            pair.remove(BASE_CURRENCY_CODE)

        # retrieve DB data
        if connection.vendor == 'sqlite':
            currencies_data = {el.currency.code: el for el in [
                CurrencyRate.objects.filter(
                    currency__code=currency_code
                ).select_related('currency').first() for currency_code in pair
            ] if el is not None}
            logger.warning(f'better do not use sqlite because twice more queries')
        else:
            currencies_data = {el.currency.code: el for el in CurrencyRate.objects.filter(
                currency__code__in=pair
            ).select_related('currency').order_by('currency', '-timestamp').distinct('currency')}

        # check currency code errors
        if len(pair) != len(currencies_data):
            logger.error(f'invalid currency code: source {source} or target {target}')
            raise ValidationError(
                detail={
                    'error': True,
                    'status': status.HTTP_400_BAD_REQUEST,
                    'message': 'invalid_currency',
                    'description': 'Invalid currency code - please try again'
                },
                code=status.HTTP_400_BAD_REQUEST
            )

        # check timestamp equality
        if len(pair) > 1 and currencies_data[source].timestamp != currencies_data[target].timestamp:
            logger.error(
                f'different timestamps: {currencies[source].timestamp} != {currencies[target].timestamp}'
            )
            raise ValidationError(
                detail={
                    'error': True,
                    'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                    'message': 'server data corruption',
                    'description': 'Invalid server data - please try again later'
                },
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # refresh currency rates
        for code, data in currencies_data.items():
            currencies[code] = data.rate

        # set timestamp
        currencies['timestamp'] = currencies_data[pair[0]].timestamp

        return currencies
