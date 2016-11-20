#!/bin/bash
echo "Constructing dev space.."

create_dev_space(){
    echo "Dev space does not exist, creating a new one..."
    local ROOT_FOLDER=tnt

    local IM_DB_FOLDER=tnt/db/im
    local MAIN_DB_FOLDER=tnt/db/app

    local IM_CONF_FOLDER=tnt/conf/im
    local IM_DB_CONF_FOLDER=tnt/conf/im-db

    local IM_LOG_FOLDER=tnt/logs/im
    local IM_DB_LOG_FOLDER=tnt/logs/im-db
    local APP_LOG_FOLDER=tnt/logs/app
    local APP_DB_LOG_FOLDER=tnt/logs/app-db



    echo Creating im configuration folder: ${IM_CONF_FOLDER}
    mkdir -p ${IM_CONF_FOLDER}
    echo Creating im db configuration folder: ${IM_DB_CONF_FOLDER}
    mkdir -p ${IM_DB_CONF_FOLDER}
    echo Creating im db folder: ${IM_DB_FOLDER}
    mkdir -p ${IM_DB_FOLDER}
    echo Creating main db folder: ${MAIN_DB_FOLDER}
    mkdir -p ${MAIN_DB_FOLDER}
    echo Creating log sub-folders: ${APP_LOG_FOLDER}, ${APP_DB_LOG_FOLDER}, ${IM_DB_LOG_FOLDER}, ${IM_LOG_FOLDER}
    mkdir -p ${APP_LOG_FOLDER} ${APP_DB_LOG_FOLDER} ${IM_DB_LOG_FOLDER} ${IM_LOG_FOLDER}

    chmod 777 -R ${ROOT_FOLDER}

    cp chat_db/ejabberd_creation.sql ${IM_DB_CONF_FOLDER}


}

[ -d ./tnt ] && echo "Main dev space folder exists, no need to re-construct" || create_dev_space

echo "building dev image"

docker-compose -f tnt-dev.yml build

#echo "image built, launching"
#
docker-compose -f tnt-dev.yml down

docker-compose -f tnt-dev.yml up

