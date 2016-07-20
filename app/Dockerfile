FROM python:2.7.11

MAINTAINER Maintainer robert

# Expose ports
EXPOSE 80

## Copy the application folder inside the container
ADD .  /var/www/tnt-backend/app
# Set the default directory where CMD will execute
WORKDIR  /var/www/tnt-backend/app

RUN pip install -r requirements.txt

CMD uwsgi --ini uwsgi-config.ini