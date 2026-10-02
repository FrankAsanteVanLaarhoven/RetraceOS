from __future__ import annotations


class RetraceError(Exception):
    def __init__(self, code: str, message: str, next_step: str, status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.next_step = next_step
        self.status = status

    def as_dict(self) -> dict[str, str]:
        return {"error": self.code, "message": self.message, "next": self.next_step}
