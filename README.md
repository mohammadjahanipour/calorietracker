# Calorietracker


### Enviroment

  Pipenv by default loads in a .env file automatically see .env.example for examples


### Dokku

**Postgres**

    dokku postgres:unlink djangodb calorietracker
    dokku postgres:destroy djangodb
    dokku postgres:create djangodb
    dokku postgres:link djangodb calorietracker

    To create superuser:

    dokku run calorietracker python mysite/manage.py createsuperuser

    To initialize test3 sampledata:

    dokku enter calorietracker
    cd mysite/
    python initializedata.py

    You will have to set test3 password via admin panel to login as test3.


### Package Documentation

<br>


  **DateTimePicker**  

  - https://monim67.github.io/django-bootstrap-datepicker-plus/configure/
  - https://github.com/monim67/django-bootstrap-datepicker-plus

<br>

**django-activity-stream**

  - https://django-activity-stream.readthedocs.io/en/latest

<br>

**Django encrypted model fields**

 - https://github.com/georgemarshall/django-cryptography


<br>

**Pinax-referrals**


  There is some funny business going on with the 004 Migration file

- https://github.com/pinax/pinax-referrals
