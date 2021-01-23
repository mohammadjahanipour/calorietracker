
**What is your situation?**

I am unable to connect to my cluster I have setup via docker swarm by following and using the official guides in a production environment, but I am successful in a "insecure" testing/ dev environment.

We have, for this instance, no firewall active or really anything else than a standard install: nginx and even the cockroach cluster overview can be accessed via: http://95.179.251.204/

I have tried various database connection configurations including the official ones with no success including the ones below with and without the commented out parts
which in my mind should work.

Including that I have also tried to follow: https://www.cockroachlabs.com/docs/stable/build-a-python-app-with-cockroachdb-django.html
which lead me to the same problem.

The main error messages I am getting when either trying to run the app or make migrations are, in order:

"""

psycopg2.OperationalError: could not connect to server: Connection refused
        Is the server running on host "95.179.251.204" and accepting
        TCP/IP connections on port 26257?

django.db.utils.OperationalError: could not connect to server: Connection refused
        Is the server running on host "95.179.251.204" and accepting
        TCP/IP connections on port 26257?

"""


Our git repository can be found on gitlab: https://gitlab.com/balugitlab/calorietracker (branch cockroach)


stack:
Debian 10
Docker - latest as of writing this (20)
Django ORM : https://pypi.org/project/django-cockroachdb/
guide which was followed : https://www.cockroachlabs.com/docs/stable/orchestrate-cockroachdb-with-docker-swarm.html
Hosting Provider: Vultr



-**Tell us about your CockroachDB cluster**


3 nodes in 3 different european datacenters (germany,france,netherlands)
data and replication factor is irrelevant at this point as we can not connect to it at all but we are planing on having less than a few G of data striped across every node

**When/how would you consider this issue resolved?**

When we can connect via a django ORM to our cluster
