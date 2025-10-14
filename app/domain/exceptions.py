class DomainException(Exception):
    """Base domain exception"""
    pass


class NoDataError(DomainException):
    """User not found"""
    pass


class AccountLockedException(DomainException):
    """Account is locked"""
    pass


class ReturnToQueueException(DomainException):
    """Error requiring task to return to queue"""
    pass


class SessionException(DomainException):
    """Session-related errors"""
    pass


class ValidationException(DomainException):
    """Validation errors"""
    pass