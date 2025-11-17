from sqlmodel import select
from src.authentication.models import Planners, Vendors
from src.authentication.schemas import UserInput
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy.exc import DatabaseError
from src.utils.auth import generate_password_hash


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

    async def signupUser(self, model, userInput: UserInput, session: AsyncSession):
        await self.checkUserExists(model, userInput, session)
        hashed_password = generate_password_hash(userInput.password)

        new_user = model(
            fullName=userInput.fullName,
            email=userInput.email,
            password_hash=hashed_password
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

    async def signupPlanner(self, plannerInput: UserInput, session: AsyncSession):
        return await self.signupUser(Planners, plannerInput, session)

    async def signupVendor(self, vendorInput: UserInput, session: AsyncSession):
        return await self.signupUser(Vendors, vendorInput, session)
