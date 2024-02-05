class ValidityError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class EntityNotFoundError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class DatabaseOperationError(Exception):
    pass
