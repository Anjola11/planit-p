"""Authentication API routes.

This module defines the REST API endpoints for user authentication workflows
including signup, OTP verification, and login. All routes are grouped under
the /auth prefix and handle request validation, business logic delegation,
and background task scheduling.
"""

from fastapi import APIRouter, Depends, status, BackgroundTasks
from src.authentication.services import AuthServices
from src.authentication.schemas import UserInput,UserCreateResponse,  VerifyOtpInput, LoginInput, LoginResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.main import get_Session
from src.emailServices.services import EmailServices

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
    otp_record = await emailServices.save_otp(user_id, session)
    
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

@authRouter.post("/verify_otp", status_code=status.HTTP_200_OK, response_model=UserCreateResponse)
async def verifyOtp(otp_input: VerifyOtpInput, background_tasks: BackgroundTasks, session: AsyncSession = Depends(get_Session)):
    """Verify user's email with OTP code.
    
    Validates the provided OTP against the stored code, marks the user's email
    as verified, and sends a welcome email. This completes the registration process.
    
    Args:
        otp_input: OTP verification data (user_id, otp code, role).
        background_tasks: FastAPI background task manager for async email sending.
        session: Database session injected via dependency injection.
        
    Returns:
        UserCreateResponse containing success status, message, and verified user data.
        
    Raises:
        HTTPException: For invalid/expired OTP or user not found.
    """
    # Verify OTP and activate user account
    verified_user = await authServices.verify_otp(otp_input, session)
    
    # Send welcome email in background (non-blocking)
    background_tasks.add_task(
        emailServices.send_welcome_email,
        verified_user.email,
        verified_user.fullName
    )
    
    if verified_user:
        return {
        "success": True,
        "message": "otp verified, proceed to login",
        "data": verified_user
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