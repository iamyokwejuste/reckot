import pytest
from django.core.exceptions import ValidationError
from unittest.mock import MagicMock
from apps.core.validators import (
    validate_image_file_size,
    validate_document_file_size,
    validate_pdf_file_size,
    MAX_IMAGE_SIZE,
    MAX_DOCUMENT_SIZE,
    MAX_PDF_SIZE,
)


class TestImageFileValidator:
    def test_accepts_small_image(self):
        file = MagicMock()
        file.size = 1024 * 1024
        validate_image_file_size(file)

    def test_rejects_large_image(self):
        file = MagicMock()
        file.size = MAX_IMAGE_SIZE + 1
        with pytest.raises(ValidationError):
            validate_image_file_size(file)

    def test_accepts_exact_limit(self):
        file = MagicMock()
        file.size = MAX_IMAGE_SIZE
        validate_image_file_size(file)


class TestDocumentFileValidator:
    def test_accepts_small_document(self):
        file = MagicMock()
        file.size = 2 * 1024 * 1024
        validate_document_file_size(file)

    def test_rejects_large_document(self):
        file = MagicMock()
        file.size = MAX_DOCUMENT_SIZE + 1
        with pytest.raises(ValidationError):
            validate_document_file_size(file)


class TestPdfFileValidator:
    def test_accepts_small_pdf(self):
        file = MagicMock()
        file.size = 5 * 1024 * 1024
        validate_pdf_file_size(file)

    def test_rejects_large_pdf(self):
        file = MagicMock()
        file.size = MAX_PDF_SIZE + 1
        with pytest.raises(ValidationError):
            validate_pdf_file_size(file)
