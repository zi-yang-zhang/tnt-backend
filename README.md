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
 "data": criteria and count
 The qualifier is limited to `equals` and `contains`
 `find: 0` means find all entries that qualifies
 
 eg.
    
    "data":{
            "name":{"equals":"something"}
            "find":0
    }
 

#### `update`
 "data": object of the resource to be updated
 "_id" must be set, otherwise will fail to update
 eg.
 
    "data":{
            "_id":"id"
            "name":"equipment 1",
            "imageURLs":"",
            "type":{
                "name":"equipment type 1"
            }
    }


## Response Structure

    {
        "success": true,
        "data":{
        },
        "exceptionMessage":""
    
    }



### Error response types

    class InvalidResourceCreationError(Exception):
        def __init__(self, param, resource_type):
            self.message = param + " is required for creating " + resource_type
    
    
    class InvalidResourceParameterError(Exception):
        def __init__(self, param, resource_type):
            self.message = param + " cannot be found in " + resource_type
    
    
    class InvalidOperationError(Exception):
        def __init__(self, param):
            self.message = "Operation " + param + " is not supported"
    
    
    class InvalidRequestError(Exception):
        def __init__(self, param):
            self.message = param + " is required for the request"
    
    
    class DuplicateResourceCreationError(Exception):
        def __init__(self, name, resource_type):
            self.message = "Resource exists with name <" + name + "> for " + resource_type


## To start

Make sure you have `docker` and `docker-compose` installed

Run `docker version` to make sure you have docker server daemon running, if not, run `start docker` with root.

Then at the root dir, run `docker-compose build`, after building, run `docker-compose up`