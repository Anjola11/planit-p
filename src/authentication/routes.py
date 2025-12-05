"""Authentication API routes.

This module defines the REST API endpoints for user authentication workflows
including signup, OTP verification, and login. All routes are grouped under
the /auth prefix and handle request validation, business logic delegation,
and background task scheduling.
"""

from fastapi import APIRouter, Depends, status, BackgroundTasks
from src.authentication.services import AuthServices
from src.authentication.schemas import UserInput,UserCreateResponse,  VerifyOtpInput, LoginInput, LoginResponse, ForgotPasswordInput, ForgotPasswordResponse, ResetPasswordInput
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.main import get_Session
from src.emailServices.services import EmailServices
from src.emailServices.schemas import OtpTypes
from src.utils.auth import create_token
from datetime import timedelta

reset_password_expiry = timedelta(minutes=5)
# Initialize router for authentication endpoints
authRouter = APIRouter()

# Initialize service instances
authServices = AuthServices()
emailServices = EmailServices()

@authRouter.post("/signup", status_code=status.HTTP_201_CREATED, response_model=UserCreateResponse)
async def signupUser(
    userInput: UserInput, 
    background_tasks: BackgroundTasks, 
    session: AsyncSession = Depends(get_Session)
):
    """Register a new user account.
    
    Creates a new user (planner or vendor), generates an OTP for email verification,
    and sends the verification email in the background. The user must verify their
    email before they can fully access the platform.
    
    Args:
        userInput: User registration data (fullName, email, password, role).
        background_tasks: FastAPI background task manager for async email sending.
        session: Database session injected via dependency injection.
        
    Returns:
        UserCreateResponse containing success status, message, and user data.
        
    Raises:
        HTTPException: Various status codes for validation errors or conflicts.
    """
    # 1. Create the user in the database
    new_user = await authServices.signupUser(userInput, session)
    user_id = new_user.user_id
    
    # 2. Generate and save OTP for email verification
    otp_record = await emailServices.save_otp(user_id, session, type = "signup")
    
    # 3. Send verification email in background (non-blocking)
    background_tasks.add_task(
        emailServices.send_email_verification_otp, 
        userInput.email, 
        otp_record.otp, 
        userInput.fullName
    )
    
    return {
        "success": True,
        "message": "signup successful, an otp has been sent to your email to verify your account",
        "data": new_user
    }

@authRouter.post("/verify_otp", status_code=status.HTTP_200_OK)
async def verifyOtp(
    otp_input: VerifyOtpInput, 
    background_tasks: BackgroundTasks, 
    session: AsyncSession = Depends(get_Session)
):
    """Verify user's email or password reset OTP."""
    
    # 1. Verify OTP
    # This returns a User object (for signup) OR a UUID (for forgot password)
    result = await authServices.verify_otp(otp_input, session)
    
    # 2. Case A: SIGNUP Logic
    if otp_input.otp_type == OtpTypes.SIGNUP:
        # Send Welcome Email (Put this back!)
        background_tasks.add_task(
            emailServices.send_welcome_email,
            result.email,     # result is a User object here
            result.fullName
        )
        
        return {
            "success": True,
            "message": "otp verified, proceed to login",
            "data": result
        }

    # 3. Case B: FORGOT PASSWORD Logic
    elif otp_input.otp_type == OtpTypes.FORGOTPASSWORD:

        reset_password_token = create_token(result, reset_password_expiry, type="reset")
        result['reset_token'] = reset_password_token
        # result is just a user_id UUID here
        return {
            "success": True,
            "message": "OTP verified successfully",
            "data": result
        }

@authRouter.post("/login",status_code=status.HTTP_200_OK, response_model=LoginResponse)
async def loginUser(loginInput: LoginInput, session: AsyncSession = Depends(get_Session)):
    """Authenticate user and generate tokens.
    
    Validates user credentials and returns JWT access and refresh tokens
    for authenticated API access. Supports both planner and vendor roles.
    
    Args:
        loginInput: Login credentials (email, password, role).
        session: Database session injected via dependency injection.
        
    Returns:
        LoginResponse containing success status, message, user data, and tokens.
        
    Raises:
        HTTPException: 400 BAD_REQUEST for invalid credentials.
    """
    # Authenticate user and generate tokens
    user = await authServices.loginUser(loginInput, session)
    
    return {
    "success": True,
    "message": "login successful",
    "data": user
    }


@authRouter.post("/forgot_password", status_code=status.HTTP_201_CREATED, response_model=ForgotPasswordResponse)
async def forgotPassword(
    forgotPasswordInput: ForgotPasswordInput, 
    background_tasks: BackgroundTasks, 
    session: AsyncSession = Depends(get_Session)
):
    
    # 1. Create the user in the database
    user = await authServices.forgotPassword(forgotPasswordInput, session)
    user_id = user.user_id
    
    # 2. Generate and save OTP for email verification
    otp_record = await emailServices.save_otp(user_id, session, type = "forgotPassword")
    
    # 3. Send verification email in background (non-blocking)
    background_tasks.add_task(
        emailServices.send_forgot_password_otp, 
       user.email, 
        otp_record.otp, 
        user.fullName
    )
    
    return {
        "success": True,
        "message": "an otp to reset password has been sent to your email",
        "data": {"user_id":user_id}
    }


@authRouter.patch("/reset_password", status_code=status.HTTP_200_OK, response_model=UserCreateResponse)
async def resetPassword( 
    resetPasswordInput: ResetPasswordInput, 
    session: AsyncSession = Depends(get_Session)
):
    
    # 1. Update the password
    user = await authServices.resetPassword(resetPasswordInput, session)
   
    return {
        "success": True,
        "message": "password reset successful, proceed to login",
        "data": user
    }
