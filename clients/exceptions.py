class AppError(Exception):
    """Expected application error, safe to show in the CLI."""


class NotFoundError(AppError):
    """City or currency was not found."""


class ExternalServiceError(AppError):
    """Network, HTTP or response contract failure."""


class HttpStatusError(ExternalServiceError):
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(f"Внешний сервис вернул HTTP {status_code}")
