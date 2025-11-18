from fastapi import APIRouter, Depends,status
from src.authentication.services import AuthServices
from src.authentication.schemas import UserInput
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.main import get_Session
from src.authentication.schemas import PlannerCreateResponse, VendorCreateResponse
authRouter = APIRouter()
authServices = AuthServices()


@authRouter.post("/sigunp/planner", status_code=status.HTTP_201_CREATED, response_model=PlannerCreateResponse)
async def signupPlanner(userInput:UserInput, session:AsyncSession = Depends(get_Session)):

    planner = await authServices.signupPlanner(userInput, session)
    return {
        "success": True,
        "message": "signup successful, an otp has been sent to your email to verify your account ",
        "data": planner
    }

@authRouter.post("/sigunp/vendor", status_code=status.HTTP_201_CREATED, response_model=VendorCreateResponse)
async def signupVendor(userInput:UserInput, session:AsyncSession = Depends(get_Session)):

    vendor = await authServices.signupVendor(userInput, session)

    return {
        "success": True,
        "message": "signup successful, an otp has been sent to your email to verify your account ",
        "data": vendor
    }