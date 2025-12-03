"""
Email service for sending emails via Zoho SMTP
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional
import secrets


class EmailService:
    """Service for sending emails via Zoho SMTP"""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        physical_address: str,
        unsubscribe_base_url: str,
        company_name: str
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.physical_address = physical_address
        self.unsubscribe_base_url = unsubscribe_base_url
        self.company_name = company_name

    def send_email(
        self,
        from_address: str,
        to_address: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        unsubscribe_token: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Send an email via Zoho SMTP

        Returns:
            Dict with 'success' (bool), 'message_id' (str or None), 'error' (str or None)
        """

        try:
            # Add CAN-SPAM footer
            body_text_with_footer = self._add_footer(body_text, unsubscribe_token, is_html=False)
            body_html_with_footer = self._add_footer(
                body_html or body_text,
                unsubscribe_token,
                is_html=True
            )

            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = from_address
            msg['To'] = to_address
            msg['Subject'] = subject
            msg['Reply-To'] = from_address

            # Attach parts
            part1 = MIMEText(body_text_with_footer, 'plain', 'utf-8')
            part2 = MIMEText(body_html_with_footer, 'html', 'utf-8')

            msg.attach(part1)
            msg.attach(part2)

            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            # Generate a mock message ID (Zoho doesn't return one via SMTP)
            message_id = f"{secrets.token_hex(8)}@zoho.com"

            return {
                'success': True,
                'message_id': message_id,
                'error': None
            }

        except Exception as e:
            return {
                'success': False,
                'message_id': None,
                'error': str(e)
            }

    def _add_footer(self, body: str, unsubscribe_token: Optional[str], is_html: bool = False) -> str:
        """Add CAN-SPAM compliant footer to email"""

        if not unsubscribe_token:
            return body

        unsubscribe_url = f"{self.unsubscribe_base_url}?token={unsubscribe_token}"

        if is_html:
            footer = f"""
<br><br>
<hr style="border: none; border-top: 1px solid #ccc; margin: 20px 0;">
<p style="font-size: 12px; color: #666;">
<strong>{self.company_name}</strong><br>
{self.physical_address}<br>
<br>
If you'd rather not receive emails like this, you can <a href="{unsubscribe_url}">unsubscribe here</a>.
</p>
"""
        else:
            footer = f"""

---

{self.company_name}
{self.physical_address}

If you'd rather not receive emails like this, you can unsubscribe here:
{unsubscribe_url}
"""

        return body + footer

    def test_connection(self) -> bool:
        """Test SMTP connection"""
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
            return True
        except Exception as e:
            print(f"SMTP connection test failed: {e}")
            return False
