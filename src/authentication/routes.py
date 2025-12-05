from fastapi import APIRouter, Depends, status, BackgroundTasks
from src.authentication.services import AuthServices
from src.authentication.schemas import UserInput,UserCreateResponse,  VerifyOtpInput, LoginInput, LoginResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.main import get_Session
from src.emailServices.services import EmailServices

authRouter = APIRouter()
authServices = AuthServices()
emailServices = EmailServices()


@authRouter.post("/signup", status_code=status.HTTP_201_CREATED, response_model=UserCreateResponse)
async def signupUser(
    userInput: UserInput, 
    background_tasks: BackgroundTasks, 
    session: AsyncSession = Depends(get_Session)
):
    # 1. Create the user
    new_user = await authServices.signupUser(userInput, session)
    user_id = new_user.user_id
    
    otp_record = await emailServices.save_otp(user_id, session)
    
    # 3. Send Email in Background
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
    verified_user = await authServices.verify_otp(otp_input, session)

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
    user = await authServices.loginUser(loginInput, session)

    return {
    "success": True,
    "message": "login successful",
    "data": user
    }