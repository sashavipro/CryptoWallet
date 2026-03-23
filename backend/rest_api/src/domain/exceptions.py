"""rest_api/src/domain/exceptions.py."""


class DomainException(Exception):  # noqa: N818
    """Base domain exception."""


class UserAlreadyExistsException(DomainException):
    """User with this email already exists."""


class UserNotFoundException(DomainException):
    """User not found."""


class InvalidCredentialsException(DomainException):
    """Invalid email or password."""
