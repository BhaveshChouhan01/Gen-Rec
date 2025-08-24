class ImageProcessingError(Exception):
    """Raised when image processing fails"""
    pass


class APIKeyMissingError(Exception):
    """Raised when required API key is missing"""
    pass


class UnsupportedImageFormatError(Exception):
    """Raised when image format is not supported"""
    pass


class ImageTooLargeError(Exception):
    """Raised when image exceeds size limits"""
    pass


class ExternalAPIError(Exception):
    """Raised when external API call fails"""
    pass


class OCRProcessingError(Exception):
    """Raised when OCR processing fails"""
    pass