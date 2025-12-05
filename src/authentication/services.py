from sqlmodel import select
from src.authentication.models import Planners, Vendors
from src.authentication.schemas import UserInput, VerifyOtpInput, LoginInput
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy.exc import DatabaseError
from src.utils.auth import generate_password_hash, verify_password_hash, create_token, decode_token
from src.authentication.models import SignupOtp, ResetPasswordOtp
from datetime import datetime, timezone, timedelta


access_token_expiry = timedelta(hours=2)
refresh_token_expiry = timedelta(days=3)

class AuthServices:

    async def checkUserExists(self, model, userInput: UserInput, session: AsyncSession):
        statement = select(model).where(model.email == userInput.email)
        result = await session.exec(statement)
        user = result.first()

        if user:
            user_selected = getattr(model, "__tablename__", "user").lower().rstrip("s")

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail= {
                    "success": False,
                    "message": f"{user_selected} already exists"}
            )
        return None

    async def signupUser(self, userInput: UserInput, session: AsyncSession):
        if userInput.role == "planner":
            model = Planners
        elif userInput.role == "vendor":
            model = Vendors
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "message": "Invalid role provided"}
            )

        await self.checkUserExists(model, userInput, session)
        hashed_password = generate_password_hash(userInput.password)

        new_user = model(
            fullName=userInput.fullName,
            email=userInput.email,
            password_hash=hashed_password,
            role=userInput.role
        )

        try:
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)

            return new_user

        except DatabaseError:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                 detail= {
                    "success": False,
                    "message": "Internal server error"
                 }

            )
    
        

    


    async def verify_otp(self, otp_input:VerifyOtpInput, session: AsyncSession):
        otp_statement = (select(SignupOtp)
                     .where(SignupOtp.user_id == otp_input.user_id)
                     .order_by(SignupOtp.created_at.desc()))
        
        result = await session.exec(otp_statement)
        latest_otp_record = result.first()

        if not latest_otp_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail={
                    "success": False,
                    "message": "no otp found for this user"
                 })
        
        if latest_otp_record.otp != otp_input.otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail={
                    "success": False,
                    "message": "Invalid OTP code",
                 })

        if datetime.now(timezone.utc) > latest_otp_record.expires:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success":False,
                    "message": "otp expired, get new otp"
                }
            )
        
        if otp_input.role == "vendor":
            model = Vendors
        elif otp_input.role == "planner":
            model = Planners
        else:
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, 
                        "message": "Invalid role provided"}
            )

        user_statement = select(model).where(model.user_id == otp_input.user_id)
        result = await session.exec(user_statement)

        user = result.first()

        if not user:
             raise HTTPException(
                 status_code=status.HTTP_404_NOT_FOUND, 
                 detail={
                    "success": False,
                    "message": "User not found"
                 })
        
        try:
            user.email_verified = True
            session.add(user)
            await session.delete(latest_otp_record)
            await session.commit()
            await session.refresh(user)
            return user

        except DatabaseError:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                 detail= {
                    "success": False, 
                    "message": "Internal server error"
                 }

            )
    
    async def loginUser(self, loginInput: LoginInput, session:AsyncSession):
       
        if loginInput.role == "vendor":
            model = Vendors
        elif loginInput.role == "planner":
            model = Planners
        else:
           
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "message": "Invalid role provided"}
            )

       
        statement = select(model).where(model.email == loginInput.email)
        result = await session.exec(statement)
        user = result.first()
        
        INVALID_CREDENTIALS = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "Invalid Credentials"}
        )

        if not user:
            raise INVALID_CREDENTIALS

       
        verified_password = verify_password_hash(loginInput.password, user.password_hash)

        if not verified_password:
            
            raise INVALID_CREDENTIALS

        user_dict = user.model_dump()
        access_token = create_token(user_dict, access_token_expiry)
        refresh_token = create_token(user_dict, refresh_token_expiry, is_refresh=True)

        user_details = {
            **user_dict, 
            'access_token': access_token,
            'refresh_token': refresh_token,
        }
        
        
        return user_details
        


        
        

        
        



