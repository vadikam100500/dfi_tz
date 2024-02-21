from app.schemas.base import EnumBaseUpper


class TransactionType(EnumBaseUpper):
    MAIN = 'MAIN'
    NESTED = 'NESTED'
    READ_ONLY = 'READ_ONLY'


class TransactionStatus(EnumBaseUpper):
    PENDING = 'PENDING'
    READY_TO_COMMIT = 'READY_TO_COMMIT'
    COMMIT = 'COMMIT'
    ROLLBACK = 'ROLLBACK'


class TransactionMethod(EnumBaseUpper):
    INSERT = 'INSERT'
    DELETE = 'DELETE'
