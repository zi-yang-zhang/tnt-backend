class RestRequestFailed(Exception):
    def __init__(self, method, url, status_code):
        self.message = "{} request to {} returns {}".format(method.__name__, url, status_code)