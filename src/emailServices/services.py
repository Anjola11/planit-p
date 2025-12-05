"""Email service layer for transactional emails.

This module handles all email-related operations including OTP generation,
template rendering, and sending transactional emails via the Brevo API.
Supports email verification and welcome emails for new users.
"""

from sqlmodel.ext.asyncio.session import AsyncSession
from src.authentication.models import SignupOtp, ResetPasswordOtp
from src.utils.otp import generate_otp
from sqlalchemy.exc import DatabaseError
from fastapi import HTTPException, status
import uuid

# Email send Imports
import brevo_python
from brevo_python.rest import ApiException
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from src.config import Config


# Setup template directory paths
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = BASE_DIR / "templates"

# Initialize Jinja2 template environment
template_env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR)
)


class EmailServices:
    """Service class for email operations.
    
    Handles OTP generation and storage, email template rendering, and
    transactional email delivery via Brevo API. Provides methods for
    common email workflows like verification and welcome emails.
    """

    def __init__(self):
        """Initialize email service with Brevo API configuration.
        
        Loads API credentials from Config and sets up the Brevo API client
        for sending transactional emails.
        """
        # Load Brevo API credentials from configuration
        self.BREVO_API_KEY = Config.BREVO_API_KEY
        self.BREVO_EMAIL = Config.BREVO_EMAIL
        self.BREVO_SENDER_NAME = Config.BREVO_SENDER_NAME

        # Configure Brevo API client
        self.configuration = brevo_python.Configuration()
        self.configuration.api_key['api-key'] = self.BREVO_API_KEY
        self.api_instance = brevo_python.TransactionalEmailsApi(brevo_python.ApiClient(self.configuration))

    async def save_otp(self,user_id: uuid.UUID, session:AsyncSession):
        """Generate and persist an OTP for user verification.
        
        Creates a new OTP record in the database associated with the given user.
        The OTP will expire after 10 minutes (configured in model default).
        
        Args:
            user_id: UUID of the user requiring OTP verification.
            session: Async database session for database operations.
            
        Returns:
            The created SignupOtp record containing the generated OTP code.
            
        Raises:
            HTTPException: 500 INTERNAL_SERVER_ERROR if database operation fails.
        """
        # Create new OTP record with generated code
        new_otp = SignupOtp(
            otp=generate_otp(),
            user_id=user_id
        )


        try:
            # Persist OTP to database
            session.add(new_otp)
            await session.commit()
            await session.refresh(new_otp)
            return new_otp
        except DatabaseError:
            # Rollback transaction on database error
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": "Internal server error"
                }
            )
        
    def render_template(self,template_name: str, payload: dict = {} ):
        """Render an HTML email template with dynamic content.
        
        Loads a Jinja2 template from the templates directory and renders it
        with the provided payload data.
        
        Args:
            template_name: Name of the template file (without .html extension).
            payload: Dictionary of variables to inject into the template.
            
        Returns:
            Rendered HTML string ready for email delivery.
            
        Raises:
            Exception: If template loading or rendering fails.
        """

        try:
            # Load and render Jinja2 template
            template = template_env.get_template(f"{template_name}.html")
            return template.render(**payload)
        except Exception as err:
            # Log error and re-raise for caller to handle
            print(f"Error rendering template '{template_name}': {err}")
            raise err
    
    
    def send_email(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """Send a transactional email via Brevo API.
        
        Base function for sending emails. Constructs the email object and
        delivers it through Brevo's transactional email service.
        
        Args:
            to_email: Recipient's email address.
            subject: Email subject line.
            html_content: HTML version of email body.
            text_content: Plain text version of email body.
            
        Returns:
            True if email was sent successfully, False otherwise.
        """
        # Skip sending if API key is not configured
        if not self.BREVO_API_KEY:
            print(f"Brevo API key not configured. Skipping email to: {to_email}")
            return False

        # Create sender object
        sender = {"name": self.BREVO_SENDER_NAME, "email": self.BREVO_EMAIL}
        
        # Create recipient list
        to = [{"email": to_email}]

        # Construct email object for Brevo API
        send_smtp_email = brevo_python.SendSmtpEmail(
            to=to,
            sender=sender,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )

        try:
            # Send email via Brevo API
            self.api_instance.send_transac_email(send_smtp_email)
            print(f"Email sent to {to_email}: {subject}")
            return True
        except ApiException as e:
            # Log API error and return failure
            print(f"Error sending email: {e}")
            return False
    
    def send_email_verification_otp(self, user_email: str, otp_code: str, user_name: str):
        """Send email verification OTP to user.
        
        Renders and sends an email containing the verification OTP code.
        The OTP expires in 10 minutes.
        
        Args:
            user_email: User's email address.
            otp_code: The verification code to send.
            user_name: User's full name for personalization.
            
        Returns:
            True if email was sent successfully, False otherwise.
        """
        # Render HTML email template with OTP details
        html = self.render_template('email-otp-verification', {
            'username': user_name,
            'otpCode': otp_code,
            'expiryTime': '10 minutes'
        })

        # Create plain text fallback version
        text_content = f"""Hello {user_name},
Your Planit verification code is: {otp_code}
This code will expire in 10 minutes. Please do not share this code with anyone.
If you didn't request this code, please ignore this email.
Best regards,
The Planit Team"""

        # Send the verification email
        return self.send_email(user_email, 'Planit - Email Verification Code', html, text_content)

    def send_welcome_email(self, user_email: str, user_name: str):
        """Send welcome email to newly verified user.
        
        Sends a welcome email after successful email verification to
        onboard the user to the platform.
        
        Args:
            user_email: User's email address.
            user_name: User's full name for personalization.
            
        Returns:
            True if email was sent successfully, False otherwise.
        """
        # Render HTML welcome email template
        html = self.render_template('welcome', {
            'username': user_name,
            'email': user_email 
        })

        # Create plain text fallback version
        text_content = f"""Welcome to Planit, {user_name}!
Thank you for verifying your email. We're excited to have you on board!
Planit helps you manage events, tasks, and everything in between.
Best regards,
The Planit Team"""

        # Send the welcome email
        return self.send_email(user_email, 'Welcome to Planit!', html, text_content)