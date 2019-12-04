from currencies.models import CurrencyRate
from simple_djangorest.celery import app


@app.task
def update_currencies():
    data = CurrencyRate.get_rates_from_api()
    CurrencyRate.save_rates_from_api(data)
