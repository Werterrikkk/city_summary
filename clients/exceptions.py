class NotFoundError(Exception):
    pass


class ExternalServiceError(Exception):
    pass


class HttpStatusError(ExternalServiceError):
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(f"Ошибка внешнего сервиса: HTTP {status_code}")
