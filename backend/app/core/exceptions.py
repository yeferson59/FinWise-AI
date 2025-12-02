from fastapi import HTTPException, status


class AuthenticationError(HTTPException):
    """Base authentication error"""

    def __init__(
        self,
        detail: str,
        error_code: str,
        status_code: int = status.HTTP_401_UNAUTHORIZED,
    ):
        super().__init__(
            status_code=status_code,
            detail=detail,
            headers={"X-Error-Code": error_code},
        )


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid"""

    def __init__(self, detail: str = "Credenciales inválidas"):
        super().__init__(
            detail=detail,
            error_code="INVALID_CREDENTIALS",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class UserNotFoundError(AuthenticationError):
    """Raised when user is not found"""

    def __init__(self, detail: str = "Usuario no encontrado"):
        super().__init__(
            detail=detail,
            error_code="USER_NOT_FOUND",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class PasswordMismatchError(HTTPException):
    """Raised when passwords don't match during registration"""

    def __init__(self, detail: str = "Las contraseñas no coinciden"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            headers={"X-Error-Code": "PASSWORD_MISMATCH"},
        )


class TermsNotAcceptedError(HTTPException):
    """Raised when terms and conditions not accepted"""

    def __init__(self, detail: str = "Debes aceptar los términos y condiciones"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            headers={"X-Error-Code": "TERMS_NOT_ACCEPTED"},
        )


class EmailAlreadyExistsError(HTTPException):
    """Raised when email already exists in database"""

    def __init__(self, detail: str = "El email ya está registrado"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            headers={"X-Error-Code": "EMAIL_ALREADY_EXISTS"},
        )


class AuthProcessError(HTTPException):
    """Raised when auth process fails"""

    def __init__(
        self, detail: str = "Error al procesar la solicitud", error_code: str = ""
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            headers={"X-Error-Code": error_code or "AUTH_PROCESS_ERROR"},
        )
