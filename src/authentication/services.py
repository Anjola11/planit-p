"""Authentication service layer.

This module implements the business logic for user authentication operations
including signup, login, and OTP verification. It handles user model selection
based on role (planner/vendor) and manages token generation for authenticated
sessions.
"""

from sqlmodel import select
from src.authentication.models import Planners, Vendors
from src.authentication.schemas import UserInput, VerifyOtpInput, LoginInput, ForgotPasswordInput, ResetPasswordInput, RenewAccessTokenInput
from src.emailServices.schemas import OtpTypes
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy.exc import DatabaseError
from src.utils.auth import generate_password_hash, verify_password_hash, create_token, decode_token
from src.authentication.models import SignupOtp, ForgotPasswordOtp
from datetime import datetime, timezone, timedelta
import uuid


# Token expiration configurations
access_token_expiry = timedelta(hours=2)
refresh_token_expiry = timedelta(days=3)
reset_password_expiry = timedelta(minutes=5)

class AuthServices:
    """Service class for authentication operations.
    
    Provides methods for user registration, login, and OTP verification.
    Handles role-based model selection and token generation.
    """

    async def checkUserExists(self, model, userInput: UserInput, session: AsyncSession):
        """Check if a user already exists in the database.
        
        Queries the database to verify whether a user with the provided email
        already exists for the given model (Planners or Vendors).
        
        Args:
            model: SQLModel class (Planners or Vendors) to query against.
            userInput: User registration data containing email to check.
            session: Async database session for executing queries.
            
        Returns:
            None if user doesn't exist.
            
        Raises:
            HTTPException: 409 CONFLICT if user already exists.
        """
        statement = select(model).where(model.email == userInput.email)
        result = await session.exec(statement)
        user = result.first()

        if user:
            # Extract singular form of table name for error message
            user_selected = getattr(model, "__tablename__", "user").lower().rstrip("s")

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=  f"{user_selected} already exists"
            )
        return None

    async def signupUser(self, userInput: UserInput, session: AsyncSession):
        """Register a new user in the system.
        
        Creates a new user account based on the provided role (planner or vendor).
        Validates uniqueness, hashes the password, and persists the user to database.
        
        Args:
            userInput: User registration data including role, email, password, etc.
            session: Async database session for database operations.
            
        Returns:
            The newly created user object with generated user_id.
            
        Raises:
            HTTPException: 400 BAD_REQUEST if role is invalid.
            HTTPException: 409 CONFLICT if user already exists.
            HTTPException: 500 INTERNAL_SERVER_ERROR if database operation fails.
        """
        # Determine the appropriate model based on user role
        if userInput.role == "planner":
            model = Planners
        elif userInput.role == "vendor":
            model = Vendors
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role provided"
            )

        # Verify user doesn't already exist
        await self.checkUserExists(model, userInput, session)
        
        # Hash password before storing
        hashed_password = generate_password_hash(userInput.password)

        # Create new user instance
        new_user = model(
            fullName=userInput.fullName,
            email=userInput.email,
            password_hash=hashed_password,
            role=userInput.role
        )

        try:
            # Persist user to database
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)

            return new_user

        except DatabaseError:
            # Rollback transaction on database error
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=  "Internal server error"
                 

            )
    
        

    


    async def verify_otp(self, otp_input:VerifyOtpInput, session: AsyncSession):
        """Verify a user's OTP and activate their account.
        
        Validates the provided OTP against the most recent code sent to the user.
        Checks for OTP expiration and marks the user's email as verified upon success.
        
        Args:
            otp_input: Contains user_id, OTP code, and role for verification.
            session: Async database session for database operations.
            
        Returns:
            The verified user object with email_verified set to True.
            
        Raises:
            HTTPException: 400 BAD_REQUEST if OTP not found, invalid, or expired.
            HTTPException: 400 BAD_REQUEST if role is invalid.
            HTTPException: 404 NOT_FOUND if user doesn't exist.
            HTTPException: 500 INTERNAL_SERVER_ERROR if database operation fails.
        """

        if otp_input.otp_type == OtpTypes.SIGNUP:
            model = SignupOtp
        elif otp_input.otp_type == OtpTypes.FORGOTPASSWORD:
            model = ForgotPasswordOtp
        # Retrieve the most recent OTP record for this user
        otp_statement = (select(model)
                     .where(model.user_id == otp_input.user_id)
                     .order_by(model.created_at.desc()))
        
        result = await session.exec(otp_statement)
        latest_otp_record = result.first()

        # Validate OTP record exists
        if not latest_otp_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail= "no otp found for this user"
                 )
        
        # Validate OTP code matches
        if latest_otp_record.otp != otp_input.otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Invalid OTP code"
                 )

        # Check if OTP has expired
        if datetime.now(timezone.utc) > latest_otp_record.expires:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="otp expired, get new otp"
                
            )
        
        # Determine the appropriate model based on user role
        if otp_input.role == "vendor":
            model = Vendors
        elif otp_input.role == "planner":
            model = Planners
        else:
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role provided"
            )
        
        if otp_input.otp_type == OtpTypes.SIGNUP:
            # Retrieve the user record
            user_statement = select(model).where(model.user_id == otp_input.user_id)
            result = await session.exec(user_statement)

            user = result.first()

            # Validate user exists
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail="User not found"
                    )
        

            try:
                # Mark user as verified and delete used OTP
                user.email_verified = True
                session.add(user)
                await session.delete(latest_otp_record)
                await session.commit()
                await session.refresh(user)
                return user

            except DatabaseError:
                # Rollback transaction on database error
                await session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error"
                    

                )
        
        if otp_input.otp_type == OtpTypes.FORGOTPASSWORD:
            try:
                await session.delete(latest_otp_record)
                await session.commit()
                return {
                    "user_id": latest_otp_record.user_id,
                    "role": otp_input.role 
                }

            except DatabaseError:
                await session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error"
                )
            
    async def loginUser(self, loginInput: LoginInput, session:AsyncSession):
        """Authenticate a user and generate access tokens.
        
        Validates user credentials and generates JWT access and refresh tokens
        for authenticated sessions. Supports both planner and vendor roles.
        
        Args:
            loginInput: Login credentials including email, password, and role.
            session: Async database session for database operations.
            
        Returns:
            Dictionary containing user details, access_token, and refresh_token.
            
        Raises:
            HTTPException: 400 BAD_REQUEST if role is invalid or credentials are wrong.
        """
        # Determine the appropriate model based on user role
        if loginInput.role == "vendor":
            model = Vendors
        elif loginInput.role == "planner":
            model = Planners
        else:
           
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role provided"
            )

        # Query user by email
        statement = select(model).where(model.email == loginInput.email)
        result = await session.exec(statement)
        user = result.first()
        
        # Reusable exception for invalid credentials
        INVALID_CREDENTIALS = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Credentials"
        )

        # Validate user exists
        if not user:
            raise INVALID_CREDENTIALS

        # Verify password hash matches
        verified_password = verify_password_hash(loginInput.password, user.password_hash)

        if not verified_password:
            
            raise INVALID_CREDENTIALS

        # Generate authentication tokens
        user_dict = user.model_dump()
        access_token = create_token(user_dict, access_token_expiry, type="access")
        refresh_token = create_token(user_dict, refresh_token_expiry, type="refresh")

        # Combine user data with tokens
        user_details = {
            **user_dict, 
            'access_token': access_token,
            'refresh_token': refresh_token,
        }
        
        
        return user_details
    
    async def forgotPassword(self, forgotPasswordInput: ForgotPasswordInput, session: AsyncSession):

         # Determine the appropriate model based on user role
        if forgotPasswordInput.role == "vendor":
            model = Vendors
        elif forgotPasswordInput.role == "planner":
            model = Planners
        else:
           
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail= "Invalid role provided"
            )

        # Query user by email
        statement = select(model).where(model.email == forgotPasswordInput.email)
        result = await session.exec(statement)
        user = result.first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail= "email is not registered"
            ) 
        
        return user
    
    
    async def resetPassword(self, resetPasswordInput: ResetPasswordInput, session: AsyncSession):
        # 1. Decode and Validate Token
        
        token_decode = decode_token(resetPasswordInput.reset_token)
        
             

        # 2. Check Token Type
        if token_decode.get('type') != "reset":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token type")

        # 3. Model Selection
        if resetPasswordInput.role == "planner":
            model = Planners
        elif resetPasswordInput.role == "vendor":
            model = Vendors
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role provided")

        # 4. Extract User ID from Token (The safest identifier)
        user_id_from_token = token_decode.get('sub')

        
        statement = select(model).where(model.user_id == uuid.UUID(user_id_from_token))
        result = await session.exec(statement)
        user = result.first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # 6. Update Password
        new_hashed_password = generate_password_hash(resetPasswordInput.new_password)
        user.password_hash = new_hashed_password

        try:
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
        except DatabaseError:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def renewAccessToken(self, renewAccessTokenInput: RenewAccessTokenInput, session: AsyncSession):
       
        refresh_token_str = renewAccessTokenInput.refresh_token
        
        token_decode = decode_token(refresh_token_str)

        if token_decode.get('type') != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid token type"
            )

        if renewAccessTokenInput.role == "planner":
            model = Planners
        elif renewAccessTokenInput.role == "vendor":
            model = Vendors
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role provided")

       
        user_id = token_decode.get("sub") 
        statement = select(model).where(model.user_id == uuid.UUID(user_id))
        result = await session.exec(statement)
        user = result.first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

       
        user_data = {
            "user_id": user.user_id,
            "email": user.email
        }

        new_token = create_token(user_data, expiry_delta=access_token_expiry, type="access")
        
        return {
            "access_token" : new_token
        }
        
       