TNT-Backend
===

Some useful tips:

To view DB in docker container, use `docker exec -it tntbackend_db_1 bash`


## Request structure:

    {
        "operation": "create",
        "data":{
        }
    
    }

`operation` can have `create`, `query`, and `update`



## To start

Make sure you have `docker` and `docker-compose` installed

Run `docker version` to make sure you have docker server daemon running, if not, run `start docker` with root.

Then at the root dir, run `docker-compose build`, after building, run `docker-compose up`