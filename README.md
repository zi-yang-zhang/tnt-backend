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
 "data": consists of chain of criteria and conditions
 
 condition can have `equals`, `contains`, `greaterThan`,`greaterOrEqualTo`, `lessOrEqualTo`, `lessThan`, `between`, `isNull`, `notNull`
 
 criteria is associate to conditions, with the field name as its first property, and values base on conditions.
 
 logical operators can have `and`, `or`, `not`
 
 limit operators can have `find`, with limit value, or -1 for all
 
 eg.
 
    "data":{
            "contains":{"name":"Robert"},
            "or":{
                    "greaterThan":{"age":20},
                    "lessThan":{"age":40},
                },
            "not":{"height":174},
            "between":{"weight":[140,180]}
            "find":-1
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