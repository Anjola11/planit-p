from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.authentication.models import Otp
from src.utils.otp import generate_otp
from sqlalchemy.exc import DatabaseError
from fastapi import HTTPException,status

class EmailServices:

    async def save_otp(self, user_id, session: AsyncSession ):
        new_otp = Otp(
            otp = generate_otp(),
            user_id=user_id
        )

        try:
            session.add(new_otp)
            await session.commit()
            await session.refresh(new_otp)
            return new_otp
        except DatabaseError:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                 detail= {
                    "success": False,
                    "message": "Internal server error"
                 }

            )