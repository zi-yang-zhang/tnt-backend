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