# Calorietracker


### Enviroment

  Pipenv by default loads in a .env file automatically see .env.example for examples
  This needs to be mirrord on deployment on Dokku

  List of required ENV Vars:

  IMPORTANT All values are type string when read in by python

      DEBUG = True
      DJANGO_LOGLEVEL = INFO

      SECRET_KEY = $z^fbe7!k&aqq79n^9lnhb^0qn+5cym*vx1n2r8m05^5=0+$)7

      # Gmail SMTP
      EMAIL_HOST_PASSWORD = 43lak

      # Cloudinary:
      CLOUDINARY_API_KEY = jl354kj
      CLOUDINARY_API_SECRET = 534lk

      # Facebook:
      ZUCC_APP_ID = 244
      ZUCC_APP_SECRET = 8e5e8

      # Discord
      DISCORD_CLIENT_ID = 768
      DISCORD_SECRET = 4OTdwm2_betA
      DISCORD_KEY = 57a72a


      STRIPE_LIVE_MODE = False
      STRIPE_TEST_PUBLIC_KEY = pk_test_51
      STRIPE_TEST_SECRET_KEY = sk_test_51
      STRIPE_LIVE_PUBLIC_KEY = pk_live_51
      STRIPE_LIVE_SECRET_KEY = sk_live_51



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


### Backup

**Cronjobs**

    Hourly DB backups

    * 1 * * * dokku postgres:export djangodb > djangodb.db



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

**Allauth**

- https://django-allauth.readthedocs.io/en/latest/index.html

**Django-friendship**

- https://github.com/revsys/django-friendship/

**Sentry**
- https://sentry.io/settings/calorietrackerio/usage/history/
