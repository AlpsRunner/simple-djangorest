import datetime

from django.urls import reverse
from rest_framework import status
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.exceptions import ValidationError
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from currencies.models import Currency, CurrencyRate
from currencies.serializers import CurrencySerializer
from simple_djangorest.settings import logger


@api_view(['GET'])
@renderer_classes([JSONRenderer])
def currencies_list(request):
    """
    List all code currencies.
    """
    currencies = Currency.objects.all()
    serializer = CurrencySerializer(currencies, many=True)
    return Response(
        data=serializer.data
    )


@api_view(['GET'])
@renderer_classes([JSONRenderer])
def currencies_convert(request, value, source, target):
    """
    Convert value from source to target currency.
    """
    try:
        value = value.replace(',', '.')
        value = float(value)
    except ValueError as e:
        logger.error(f'{e}')
        raise ValidationError(
            detail={
                'error': True,
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'invalid_amount',
                'description': 'Invalid currency amount - please try again'
            },
            code=status.HTTP_400_BAD_REQUEST
        )

    if source == target:
        timestamp = int(datetime.datetime.now().timestamp())
        rate = 1
        response = value
    else:
        currencies = CurrencyRate.get_pair_data(source, target)
        timestamp = currencies['timestamp']
        rate = currencies[target] / currencies[source]
        response = value * rate

    return Response(
        data={"request": {
            "query": reverse(
                'api:currencies_convert',
                kwargs={
                    'value': value,
                    'source': source,
                    'target': target
                }),
            "amount": value,
            "from": source,
            "to": target
        },
            "meta": {
                "timestamp": timestamp,
                "rate": rate
            },
            "response": response},
    )
