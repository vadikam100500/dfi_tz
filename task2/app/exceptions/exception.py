class EntityException(Exception):  # noqa N818
    def __init__(self, message: str):
        self.message = message


class NotFoundEntity(EntityException):  # noqa N818
    pass


class ProcessingException(EntityException):  # noqa N818
    pass
