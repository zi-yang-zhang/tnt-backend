TNT-Backend
===

Some useful tips:

To view DB in docker container, use `docker exec -it tntbackend_db_1 bash`

## User Restriction Level(Privilege is inclusive)
*DBA*:**0**[Manage all DB(Restoration, Backup)]

*SystemAdmin*:**1**[Manage all collection(Delete Collection, User data, Revoke User privilege, Access Admin user DB)]

*Admin*:**2**[Manage Resource data(CRUD Resource data)]

*PowerUser(Gym, coach)*:**3**[Access Resource Data(Create and Read Resource data)]

*User*:**4**[Access Resource Data(Read Resource data)]

*Guest*:**5**[Restricted Access Resource Data(Read Resource data)]

## Authentication scheme:
### Admin
#### Request
    scheme='tnt-admin-auth-scheme', realm='admin'
    Auth header(base 64 encoded)
    {
        username:password
    }
    password is verified against sha256 encrypted string from database
#### Response
    jwt with claims={'exp': '', 'iat': '', 'user': ''}
    expiry in a month.
    
### User (OAuth 2)

**On app start**

*Request*

Get Public Key
Request for Server public key

    Get /api/gpk

*Response*

    {"publicKey":''}
    
    
#### Wechat OAuth

![alt auth diagram](wechat_auth.png)

**Login**

    /api/wechat_auth

*Request*

    public key encrypted
    POST
    {
        "code":''
    }
    
#### Password based Authentication

**Registration**

    /api/register

*Request*

    public key encrypted
    POST
    {
        "username":'',
        "password":'',
        "clientPublicKey":'',
        "deviceName":''
    }
    
*Response*

    {
        "success":'',
        "data":
        {
                "token_type":"bearer",
                "access_token":"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiVlx1MDAxNcKbwoNUwoonbFPCu8KhwrYiLCJpYXQiOjE0NDQyNjI1NDMsImV4cCI6MTQ0NDI2MjU2M30.MldruS1PvZaRZIJR4legQaauQ3_DYKxxP2rFnD37Ip4",
                "refresh_token":"fdb8fdbecf1d03ce5e6125c067733c0d51de209c"
        }
    }
    

**Authentication**

    /api/auth

*Request*

    GET
    scheme='tnt-user-auth-scheme', realm='user'
    public key encrypted in header
    {
        "type":"password",
        "username":'',
        "password":'',
        "clientPublicKey":'',
        "deviceName":''
    }
    
    
*Response*

    {
        "success":'',
        "data":
        {
                "token_type":"bearer",
                "access_token":"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiVlx1MDAxNcKbwoNUwoonbFPCu8KhwrYiLCJpYXQiOjE0NDQyNjI1NDMsImV4cCI6MTQ0NDI2MjU2M30.MldruS1PvZaRZIJR4legQaauQ3_DYKxxP2rFnD37Ip4",
                "refresh_token":"fdb8fdbecf1d03ce5e6125c067733c0d51de209c"
        }
    }

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