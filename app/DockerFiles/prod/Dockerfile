FROM python:2.7.11

MAINTAINER Maintainer robert

# Expose ports
EXPOSE 8000
ADD requirements.txt /
RUN pip install -r requirements.txt
RUN rm requirements.txt
## Copy the application folder inside the container
ADD .  /app
# Set the default directory where CMD will execute
WORKDIR  /app

ENV setting="settings.py"

CMD gunicorn -b 0.0.0.0:8000 -w 4 app:application
