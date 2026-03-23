class ApplicationError(Exception):
    # Base class for application errors
    pass


class APIError(ApplicationError):
    # Something went wrong talking to the API
    pass


class StorageError(ApplicationError):
    # Something went wrong reading or writing data
    pass


class ParseError(ApplicationError):
    # Seomthing went wrong parsing the API response
    pass
