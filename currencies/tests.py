import itertools

from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status

from currencies.serializers import CurrencySerializer
from simple_djangorest.settings import BASE_CURRENCY_CODE
from .models import Currency, CurrencyRate

# initialize the APIClient app
client = Client()

# currencies codes and names
currencies = {
    'CZK': 'Czech Republic Koruna',
    'EUR': 'Euro',
    'PLN': 'Polish Zloty',
    'USD': 'United States Dollar'
}

# currencies rates
currencies_rates = {"disclaimer": "Usage subject to terms: https://openexchangerates.org/terms",
                    "license": "https://openexchangerates.org/license",
                    "timestamp": 1575309600,
                    "base": BASE_CURRENCY_CODE,
                    "rates": {"CZK": 23.0653, "EUR": 0.9029, "PLN": 3.871849}}


class GetAllCurrenciesTest(TestCase):
    """ Test module for GET all currencies API """

    def setUp(self):
        currencies_objs = []
        for currency in currencies.items():
            currencies_objs.append(Currency(code=currency[0], name=currency[1]))
        Currency.objects.bulk_create(currencies_objs)

    def test_get_all_currencies(self):
        # get API response
        response = client.get(reverse('api:currencies_list'))
        # get data from db
        currencies = Currency.objects.all()
        serializer = CurrencySerializer(currencies, many=True)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CurrencyLoadFromApiTest(TestCase):
    """ Test module for load currencies data from API """

    def test_get_currencies_from_api(self):
        # get data from API
        data = Currency.get_currencies_from_api()
        data_sliced = {key: val for key, val in data[:len(currencies)]}
        self.assertEqual(data_sliced, currencies)

    def test_save_currencies_from_api(self):
        # save data to DB
        Currency.save_currencies_from_api(currencies.items())
        db_objs = {el.code: el.name for el in Currency.objects.filter(code__in=currencies.keys())}
        self.assertEqual(db_objs, currencies)


class CurrencyRateLoadFromApiTest(TestCase):
    """ Test module for load currencies rate from API """

    def setUp(self):
        Currency.save_currencies_from_api(currencies.items())

    def test_get_currencies_from_api(self):
        # get data from API
        data = CurrencyRate.get_rates_from_api()
        self.assertIsNotNone(data)
        self.assertTrue('timestamp' in data.keys())
        self.assertTrue('base' in data.keys())
        self.assertEqual(data['base'], BASE_CURRENCY_CODE)
        self.assertTrue('rates' in data.keys())
        for key in currencies_rates['rates']:
            self.assertTrue(key in data['rates'].keys())

    def test_save_currencies_from_api(self):
        # save data to DB
        result = CurrencyRate.save_rates_from_api(currencies_rates)
        self.assertTrue(result)
        db_objs = {
            el.currency.code: el for el in
            CurrencyRate.objects.filter(
                currency__code__in=currencies_rates['rates'].keys()
            ).select_related()
        }
        for code, rate in currencies_rates['rates'].items():
            self.assertEqual(db_objs[code].rate, rate)

        for val in db_objs.values():
            self.assertEqual(val.timestamp, currencies_rates['timestamp'])


class ConvertCurrenciesTest(TestCase):
    """ Test module for convert currencies API """

    def setUp(self):
        Currency.save_currencies_from_api(currencies.items())
        CurrencyRate.save_rates_from_api(currencies_rates)

    def test_get_pair_data(self):
        all_pairs = itertools.product(currencies.keys(), currencies.keys(), repeat=1)
        for pair in all_pairs:
            # pass same codes
            if len(set(pair)) > 1:
                data = CurrencyRate.get_pair_data(*pair)
                for code in pair:
                    if code == BASE_CURRENCY_CODE:
                        self.assertEqual(data[code], 1)
                    else:
                        self.assertEqual(data[code], currencies_rates['rates'][code])

    def test_convert_diff_currencies(self):
        all_pairs = itertools.product(currencies.keys(), currencies.keys(), repeat=1)
        for value in (0, 5.1489, 50, 1589):
            for source, target in all_pairs:
                # pass same codes
                if source != target:
                    # get API response
                    response = client.get(reverse(
                        'api:currencies_convert',
                        kwargs={
                            'value': value,
                            'source': source,
                            'target': target
                        }))
                    # calc values
                    rate = currencies_rates['rates'][target] if target != BASE_CURRENCY_CODE else 1
                    rate /= currencies_rates['rates'][source] if source != BASE_CURRENCY_CODE else 1
                    result = value * rate

                    self.assertEqual(response.status_code, status.HTTP_200_OK)
                    self.assertEqual(response.data['response'], result)
                    self.assertEqual(response.data['meta']['rate'], rate)

    def test_convert_same_currencies(self):
        for value in (0, 5.1489, 50, 1589):
            for source in currencies.keys():
                target = source
                # get API response
                response = client.get(reverse(
                    'api:currencies_convert',
                    kwargs={
                        'value': value,
                        'source': source,
                        'target': target
                    }))
                # calc values
                rate = 1
                result = value

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data['response'], result)
                self.assertEqual(response.data['meta']['rate'], rate)

    def test_convert_currencies_invalid_amount(self):
        all_pairs = itertools.product(currencies.keys(), currencies.keys(), repeat=1)
        value = '157.g371'
        for source, target in all_pairs:
            # get API response
            response = client.get(reverse(
                'api:currencies_convert',
                kwargs={
                    'value': value,
                    'source': source,
                    'target': target
                }))

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertTrue(response.data['error'])
            self.assertEqual(response.data['status'], str(status.HTTP_400_BAD_REQUEST))
            self.assertEqual(response.data['message'], 'invalid_amount')
            self.assertEqual(response.data['description'], 'Invalid currency amount - please try again')

    def test_convert_currencies_invalid_currency(self):
        value = 157.371
        # wrong source
        source = 'AAA'
        for target in currencies.keys():
            # get API response
            response = client.get(reverse(
                'api:currencies_convert',
                kwargs={
                    'value': value,
                    'source': source,
                    'target': target
                }))

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertTrue(response.data['error'])
            self.assertEqual(response.data['status'], str(status.HTTP_400_BAD_REQUEST))
            self.assertEqual(response.data['message'], 'invalid_currency')
            self.assertEqual(response.data['description'], 'Invalid currency code - please try again')

        # wrong target
        target = 'AAA'
        for source in currencies.keys():
            # get API response
            response = client.get(reverse(
                'api:currencies_convert',
                kwargs={
                    'value': value,
                    'source': source,
                    'target': target
                }))

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertTrue(response.data['error'])
            self.assertEqual(response.data['status'], str(status.HTTP_400_BAD_REQUEST))
            self.assertEqual(response.data['message'], 'invalid_currency')
            self.assertEqual(response.data['description'], 'Invalid currency code - please try again')
