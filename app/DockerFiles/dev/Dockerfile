FROM python:2.7.11

MAINTAINER Robert Zhang
EXPOSE 80

## Copy the application folder inside the container
ADD .  /app
# Set the default directory where CMD will execute
WORKDIR  /app

ENV setting="settings-dev.py"
ENV FLASK_DEBUG=1
ENV CHAT_SERVER_ADMIN=admin
ENV CHAT_SERVER_ADMIN_PW=12345
ENV CHAT_SERVER="http://openfire:9090"


RUN pip install -r requirements.txt

CMD python app.py
