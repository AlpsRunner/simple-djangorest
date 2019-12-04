from django.urls import re_path

import currencies.views as currencies

app_name = 'currencies'

urlpatterns = [
    re_path(
        r'currencies/$',
        currencies.currencies_list,
        name='currencies_list'
    ),
    re_path(
        r'convert/(?P<value>.*)/(?P<source>\w{3})/(?P<target>\w{3})/$',
        currencies.currencies_convert,
        name='currencies_convert'
    ),
]
