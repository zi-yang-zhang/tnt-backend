def prettify_bson(bson_string):
    bson_string['_id'] = bson_string['_id']['$oid']
    return bson_string
