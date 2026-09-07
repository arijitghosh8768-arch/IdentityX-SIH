"""Custom exception classes for consistent error handling across the API."""

from fastapi import HTTPException, status


class IdentityXError(Exception):
    """Base exception for all IdentityX errors."""

    def __init__(self, message: str = "An unexpected error occurred", details: str = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class DocumentProcessingError(IdentityXError):
    """Raised when a document cannot be processed (bad format, corrupt, etc.)."""
    pass


class OCRError(IdentityXError):
    """Raised when the OCR engine fails to extract text."""
    pass


class FaceVerificationError(IdentityXError):
    """Raised when face verification encounters an irrecoverable error."""
    pass


class BlockchainError(IdentityXError):
    """Raised when blockchain logging or verification fails."""
    pass


class DocumentNotFoundError(IdentityXError):
    """Raised when a requested document/report does not exist in the database."""
    pass


# ---------------------------------------------------------------------------
# FastAPI exception handlers — register these in main.py via app.exception_handler
# ---------------------------------------------------------------------------

def identityx_error_handler(request, exc: IdentityXError):
    """Generic handler for all IdentityX custom exceptions."""
    return {
        "error": exc.message,
        "details": exc.details,
        "type": type(exc).__name__,
    }


def register_exception_handlers(app):
    """Register custom exception handlers with the FastAPI application."""
    from fastapi.responses import JSONResponse

    @app.exception_handler(DocumentProcessingError)
    async def _doc_processing_handler(request, exc: DocumentProcessingError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": exc.message, "details": exc.details, "type": "DocumentProcessingError"},
        )

    @app.exception_handler(OCRError)
    async def _ocr_handler(request, exc: OCRError):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": exc.message, "details": exc.details, "type": "OCRError"},
        )

    @app.exception_handler(FaceVerificationError)
    async def _face_handler(request, exc: FaceVerificationError):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": exc.message, "details": exc.details, "type": "FaceVerificationError"},
        )

    @app.exception_handler(BlockchainError)
    async def _blockchain_handler(request, exc: BlockchainError):
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"error": exc.message, "details": exc.details, "type": "BlockchainError"},
        )

    @app.exception_handler(DocumentNotFoundError)
    async def _not_found_handler(request, exc: DocumentNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": exc.message, "details": exc.details, "type": "DocumentNotFoundError"},
        )
