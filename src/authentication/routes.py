from fastapi import APIRouter, Depends, status, BackgroundTasks
from src.authentication.services import AuthServices
from src.authentication.schemas import UserInput, PlannerCreateResponse, VendorCreateResponse
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
        emailServices.send_otp_email, 
        userInput.email, 
        otp_record.otp, 
        userInput.username
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
    # 1. Create the user
    vendor = await authServices.signupVendor(userInput, session)
    vendor_id = vendor.user_id
    
    # 2. Generate and Save OTP
    otp_record = await emailServices.save_otp(vendor_id, session)

    # 3. Send Email in Background
    background_tasks.add_task(
        emailServices.send_otp_email, 
        userInput.email, 
        otp_record.otp, 
        userInput.fullName
    )

    return {
        "success": True,
        "message": "signup successful, an otp has been sent to your email to verify your account",
        "data": vendor
    }