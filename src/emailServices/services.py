from sqlmodel.ext.asyncio.session import AsyncSession
from src.authentication.models import Otp
from src.utils.otp import generate_otp
from sqlalchemy.exc import DatabaseError
from fastapi import HTTPException, status
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from src.config import Config

# --- Initialize Jinja2 Template Engine Globally ---
# This ensures we don't reload templates on every email sent
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = BASE_DIR / "templates"

template_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(['html', 'xml'])
)

class EmailServices:
    def __init__(self):
        self.brevo_api_key = Config.BREVO_API_KEY
        self.sender_email = Config.BREVO_EMAIL
        self.sender_name = "Planit"
        
        # Initialize Brevo API Client
        self.configuration = sib_api_v3_sdk.Configuration()
        self.configuration.api_key['api-key'] = self.brevo_api_key
        self.api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(self.configuration))

    async def save_otp(self, user_id: str, session: AsyncSession):
        """
        Generate and save an OTP to the database.
        Returns the OTP object (containing the code).
        """
        new_otp = Otp(
            otp=generate_otp(),
            user_id=user_id
        )

        try:
            session.add(new_otp)
            await session.commit()
            await session.refresh(new_otp)
            return new_otp
        except DatabaseError:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": "Internal server error"
                }
            )

    def render_template(self, template_name: str, payload: dict = {}) -> str:
        """
        Render email template with Jinja2
        """
        try:
            # Uses the global template_env defined at the top
            # Assumes files are named like 'otp-verification.html'
            template = template_env.get_template(f"{template_name}.html")
            return template.render(**payload)
        except Exception as err:
            print(f"Error rendering template '{template_name}': {err}")
            raise err

    def send_email(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """
        Base function to send emails via Brevo API
        """
        if not self.brevo_api_key:
            print(f"Brevo API key not configured. Skipping email to: {to_email}")
            return False

        # Create the sender object
        sender = {"name": self.sender_name, "email": self.sender_email}
        
        # Create the recipient list
        to = [{"email": to_email}]

        # Create the email object
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=to,
            sender=sender,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )

        try:
            # Note: This is a blocking call (synchronous)
            self.api_instance.send_transac_email(send_smtp_email)
            print(f"Email sent to {to_email}: {subject}")
            return True
        except ApiException as e:
            print(f"Error sending email: {e}")
            return False

    async def send_otp_email(self, user_email: str, otp_code: str, user_name: str):
        """
        Send OTP verification email
        """
        # Renders src/templates/otp-verification.html
        html = self.render_template('otp-verification', {
            'username': user_name,
            'otpCode': otp_code,
            'expiryTime': '10 minutes'
        })

        text_content = f"""Hello {user_name},
Your Planit verification code is: {otp_code}
This code will expire in 10 minutes. Please do not share this code with anyone.
If you didn't request this code, please ignore this email.
Best regards,
The Planit Team"""

        return self.send_email(user_email, 'Planit - Email Verification Code', html, text_content)

    async def send_welcome_email(self, user_email: str, user_name: str):
        """
        Send Welcome email
        """
        # Renders src/templates/welcome.html
        html = self.render_template('welcome', {
            'username': user_name,
            'email': user_email # passing email just in case template uses it later
        })

        text_content = f"""Welcome to Planit, {user_name}!
Thank you for verifying your email. We're excited to have you on board!
Planit helps you manage events, tasks, and everything in between.
Best regards,
The Planit Team"""

        return self.send_email(user_email, 'Welcome to Planit!', html, text_content)