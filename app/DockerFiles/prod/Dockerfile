FROM python:2.7.11

MAINTAINER Maintainer robert

# Expose ports
EXPOSE 8000

## Copy the application folder inside the container
ADD .  /app
# Set the default directory where CMD will execute
WORKDIR  /app

ENV setting="settings.py"

RUN pip install -r requirements.txt

CMD gunicorn -b 0.0.0.0:8000 -w 4 app:application
