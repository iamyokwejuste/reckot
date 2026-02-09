from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

ALLOWED_IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]
ALLOWED_DOCUMENT_EXTENSIONS = ["jpg", "jpeg", "png", "webp", "pdf"]
ALLOWED_PDF_EXTENSIONS = ["pdf"]

MAX_IMAGE_SIZE = 5 * 1024 * 1024
MAX_DOCUMENT_SIZE = 10 * 1024 * 1024
MAX_PDF_SIZE = 20 * 1024 * 1024


def validate_image_file_size(value):
    if value.size > MAX_IMAGE_SIZE:
        raise ValidationError(
            _("Image file size must be under %(limit)s MB.")
            % {"limit": MAX_IMAGE_SIZE // (1024 * 1024)}
        )


def validate_document_file_size(value):
    if value.size > MAX_DOCUMENT_SIZE:
        raise ValidationError(
            _("Document file size must be under %(limit)s MB.")
            % {"limit": MAX_DOCUMENT_SIZE // (1024 * 1024)}
        )


def validate_pdf_file_size(value):
    if value.size > MAX_PDF_SIZE:
        raise ValidationError(
            _("PDF file size must be under %(limit)s MB.")
            % {"limit": MAX_PDF_SIZE // (1024 * 1024)}
        )
