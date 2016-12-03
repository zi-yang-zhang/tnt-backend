#!/usr/bin/env bash

#!/bin/bash
echo "Constructing data folders.."

create(){
    echo "Data folders does not exist, creating a new one..."
    local ROOT_FOLDER=~/tnt-data

    local MAIN_DB_FOLDER=~/tnt-data/db/app

    local APP_LOG_FOLDER=~/tnt-data/logs/app
    local APP_DB_LOG_FOLDER=~/tnt-data/logs/app-db



    echo Creating main db folder: ${MAIN_DB_FOLDER}
    mkdir -p ${MAIN_DB_FOLDER}
    echo Creating log sub-folders: ${APP_LOG_FOLDER}, ${APP_DB_LOG_FOLDER}
    mkdir -p ${APP_LOG_FOLDER} ${APP_DB_LOG_FOLDER}

    chmod 777 -R ${ROOT_FOLDER}

}

[ -d ~/tnt-data ] && echo "Main data folders exists, no need to re-construct" || create

echo "building image.."

docker-compose -f tnt-prod.yml build

echo "image built, checking if old instances running..."

docker-compose -f tnt-prod.yml down

echo "Launching....."


docker-compose -f tnt-prod.yml up
