# simple_djangorest
simple project to learn how to implement REST API using Django


# Dependecies

* Celery 4.3.1
* Django 2.2
* Django REST 3.10
* Redis 4.0.9


# How to install:
```
  git clone https://github.com/AlpsRunner/simple_djangorest.git
  cd simple_djangorest
  
  pip3 install -r requirements.txt

  export EXCHANGERATES_API_APP_ID='<your APP ID>'
  export EXCHANGERATES_DB_USER='<your DB user name>'
  export EXCHANGERATES_DB_PASS='<your DB user pass>'

  python3 manage.py makemigrations
  python3 manage.py migrate
  python3 manage.py fill_db
```

# How to run tests:
```
  python3 manage.py test
```


# How to run in dev mode:
```
  To run celery update currency rates tasks every day:
    celery -A simple_djangorest worker -l info -B  
  
  To run REST API:
    python3 manage.py runserver 0.0.0.0:8000
```

# How to make requests:
```
  To get all currencies list:
    <server address>/api/currencies/  

  Example:
      127.0.0.1:8000/api/currencies/
            [
                {
                    "code": "CZK",
                    "alias": "Czech koruna"
                },
                {
                    "code": "EUR",
                    "alias": "Euro"
                },
                {
                    "code": "PLN",
                    "alias": "Polish złoty"
                },
                {
                    "code": "USD",
                    "alias": "US dollar"
                }
            ]
      
  
  To convert currencies:
    <server address>/api/convert/value/<source currency>/<target currency>/
  
  Example:
      127.0.0.1:8000/api/convert/157.371/PLN/CZK/
            {
                "request": {
                    "query": "/api/convert/157.371/PLN/CZK/",
                    "amount": 157.371,
                    "from": "PLN",
                    "to": "CZK"
                },
                "meta": {
                    "timestamp": 1575320400,
                    "rate": 5.958531809737713
                },
                "response": 937.7001094302337
            }
  
```
