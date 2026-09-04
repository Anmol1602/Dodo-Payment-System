from typing import Any, Optional
from fastapi import HTTPException, status


class ServiceException(HTTPException):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(
            status_code=status_code,
            detail={
                "error": {
                    "code": code,
                    "message": message,
                    "details": self.details
                }
            }
        )


class AuthenticationError(ServiceException):
    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="AUTHENTICATION_FAILED",
            message=message
        )


class ResourceNotFoundError(ServiceException):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=f"{resource} with id '{resource_id}' was not found.",
            details={"resource": resource, "id": resource_id}
        )


class InvalidStateTransitionError(ServiceException):
    def __init__(self, current_state: str, action: str, reason: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="INVALID_STATE_TRANSITION",
            message=f"Cannot execute '{action}' on invoice in state '{current_state}': {reason}",
            details={"current_state": current_state, "action": action}
        )


class IdempotencyConflictError(ServiceException):
    def __init__(self, key: str, message: str = "Idempotency key reused with mismatched payload or concurrent request in progress"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="IDEMPOTENCY_CONFLICT",
            message=message,
            details={"idempotency_key": key}
        )


class MissingIdempotencyKeyError(ServiceException):
    def __init__(self, message: str = "The 'Idempotency-Key' HTTP header is mandatory for payment attempts."):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="MISSING_IDEMPOTENCY_KEY",
            message=message,
            details={}
        )


class PaymentFailedError(ServiceException):
    def __init__(
        self,
        failure_code: str,
        message: str,
        payment_attempt_id: str,
        invoice_id: str,
        invoice_state: str
    ):
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            code="PAYMENT_FAILED",
            message=message,
            details={
                "payment_attempt_id": payment_attempt_id,
                "invoice_id": invoice_id,
                "failure_code": failure_code,
                "invoice_state": invoice_state
            }
        )


class PSPTimeoutError(ServiceException):
    def __init__(self, payment_attempt_id: str, invoice_id: str, invoice_state: str):
        super().__init__(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            code="PSP_TIMEOUT",
            message="Payment processor timed out. Payment attempt recorded in pending state.",
            details={
                "payment_attempt_id": payment_attempt_id,
                "invoice_id": invoice_id,
                "invoice_state": invoice_state
            }
        )


class PSPNetworkError(ServiceException):
    def __init__(self, payment_attempt_id: str, invoice_id: str, invoice_state: str, error_detail: str):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="PSP_NETWORK_ERROR",
            message=f"Payment processor network error: {error_detail}",
            details={
                "payment_attempt_id": payment_attempt_id,
                "invoice_id": invoice_id,
                "invoice_state": invoice_state
            }
        )
