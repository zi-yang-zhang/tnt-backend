FROM rroemhild/ejabberd
MAINTAINER Robert Zhang
USER root
EXPOSE 5320 4560 5222 5269 5280 5443
RUN apt-get update \
    && apt-get install -y python-pip erlang-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get purge -y


RUN pip install -U pip setuptools \
    && pip install 'requests==2.11.0'

COPY ./ejabberd.yml.tpl /opt/ejabberd/conf/ejabberd.yml.tpl
COPY ./auth_ext_core.py $EJABBERD_HOME/scripts/lib/auth_ext_core.py
RUN chmod a+rx $EJABBERD_HOME/scripts/lib/auth_ext_core.py

#COPY ./21_install_restful.sh $EJABBERD_HOME/scripts/pre
#RUN chmod a+rx $EJABBERD_HOME/scripts/pre/21_install_restful.sh
#RUN chown $EJABBERD_USER $EJABBERD_HOME/scripts/pre/21_install_restful.sh


USER $EJABBERD_USER
