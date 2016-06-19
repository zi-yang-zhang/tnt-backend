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

`data` is differ from operation:

### `data` structure for `operation`

#### `create`
 "data": object of the resource to be created
 
 eg.
 
    "data":{
            "name":"equipment 1",
            "imageURLs":"",
            "type":{
                "name":"equipment type 1"
            }
    }
        
#### `query`
 "data": criteria and conditions based on resources
 
 criteria consists of the following structure(mongodb query style):
 
    "fieldName":{"qualifier":"criteria"}
 
 Equipment: name or type
 
 eg.
    
    "data":{
            "name":{"equals":"something"}
            "find":0
    }
 

#### `update`
 "data": object of the resource to be updated
 eg.
 
    "data":{
            "name":"equipment 1",
            "imageURLs":"",
            "type":{
                "name":"equipment type 1"
            }
    }

## To start

Make sure you have `docker` and `docker-compose` installed

Run `docker version` to make sure you have docker server daemon running, if not, run `start docker` with root.

Then at the root dir, run `docker-compose build`, after building, run `docker-compose up`