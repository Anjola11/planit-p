from fastapi import APIRouter, Depends, status, BackgroundTasks
from src.authentication.services import AuthServices
from src.authentication.schemas import UserInput, PlannerCreateResponse, VendorCreateResponse, VerifyOtpInput
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.main import get_Session
from src.emailServices.services import EmailServices

authRouter = APIRouter()
authServices = AuthServices()
emailServices = EmailServices()


@authRouter.post("/signup/planner", status_code=status.HTTP_201_CREATED, response_model=PlannerCreateResponse)
async def signupPlanner(
    userInput: UserInput, 
    background_tasks: BackgroundTasks, 
    session: AsyncSession = Depends(get_Session)
):
    # 1. Create the user
    planner = await authServices.signupPlanner(userInput, session)
    planner_id = planner.user_id
    
    otp_record = await emailServices.save_otp(planner_id, session)
    
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
        "data": planner
    }

@authRouter.post("/signup/vendor", status_code=status.HTTP_201_CREATED, response_model=VendorCreateResponse)
async def signupVendor(
    userInput: UserInput, 
    background_tasks: BackgroundTasks, 
    session: AsyncSession = Depends(get_Session)
):

    vendor = await authServices.signupVendor(userInput, session)
    vendor_id = vendor.user_id
    
    otp_record = await emailServices.save_otp(vendor_id, session)

    background_tasks.add_task(
        emailServices.send_email_verification_otp, 
        userInput.email, 
        otp_record.otp, 
        userInput.fullName
    )
    return {
        "success": True,
        "message": "signup successful, an otp has been sent to your email to verify your account",
        "data": vendor
    }

@authRouter.post("/verify_otp", status_code=status.HTTP_200_OK, response_model=VendorCreateResponse)
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
