from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.db.main import init_db
from src.authentication.routes import authRouter
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n---Server Started---\n")
    await init_db()
    yield
    print("---Server Closed---")

app = FastAPI(
    title="Planit API",
    description="Endpoints for planit event management Platform",
    lifespan = lifespan
)

@app.get("/")
def health_check():
    return{
        "status": "Success",
        "message": "Server Working"
    }




@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": False,
            "message": exc.detail,
            "data": None
        }
    )


app.include_router(authRouter, prefix="/planit")