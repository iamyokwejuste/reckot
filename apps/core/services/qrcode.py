import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from io import BytesIO
import base64
from django.conf import settings


class QRCodeService:
    """Service for generating QR codes for tickets."""

    @staticmethod
    def generate_ticket_qr(ticket_code: str, size: int = 10) -> BytesIO:
        """
        Generate a QR code for a ticket.

        Args:
            ticket_code: The unique ticket code (UUID)
            size: Box size for the QR code

        Returns:
            BytesIO buffer containing the PNG image
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=size,
            border=2,
        )

        # Create the check-in URL
        checkin_url = f"{settings.SITE_URL}/checkin/verify/{ticket_code}/"
        qr.add_data(checkin_url)
        qr.make(fit=True)

        # Create styled image with rounded modules
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=RoundedModuleDrawer(),
            fill_color="#09090b",
            back_color="#ffffff",
        )

        # Save to BytesIO
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        return buffer

    @staticmethod
    def generate_ticket_qr_base64(ticket_code: str) -> str:
        """
        Generate a QR code and return as base64 string.

        Args:
            ticket_code: The unique ticket code (UUID)

        Returns:
            Base64 encoded string of the PNG image
        """
        buffer = QRCodeService.generate_ticket_qr(ticket_code)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    @staticmethod
    def generate_booking_qr(booking_id: int, ticket_codes: list[str]) -> BytesIO:
        """
        Generate a combined QR code for all tickets in a booking.

        Args:
            booking_id: The booking ID
            ticket_codes: List of ticket codes

        Returns:
            BytesIO buffer containing the PNG image
        """
        qr = qrcode.QRCode(
            version=2,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=2,
        )

        qr_data = f"RECKOT:B{booking_id}:" + ",".join(str(code)[:8] for code in ticket_codes)
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=RoundedModuleDrawer(),
            fill_color="#09090b",
            back_color="#ffffff",
        )

        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        return buffer
