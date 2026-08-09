import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlmodel import Session, select

from database import create_db_and_tables, get_session
from models import (
    StatusEnum,
    Token,
    User,
    UserCreate,
    UserRead,
    VisaApplication,
    VisaApplicationCreate,
    VisaApplicationRead,
)

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is required")

ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    lifespan=lifespan,
    title="E-Visa System",
    description="Online visa processing and application management system.",
    version="1.0.0",
    contact={"name": "ahmeddotrs", "email": "contactme@example.com"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str | None = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user


class AppHeaders(BaseModel):
    user_agent: str | None


@app.get("/", status_code=status.HTTP_200_OK)
def root(
    app_headers: Annotated[AppHeaders, Header()],
):
    return {"message": "Welcome to E-Visa System", "user-agent": app_headers.user_agent}


@app.post("/register", response_model=UserRead, tags=["Auth"])
def register(user: UserCreate, session: Session = Depends(get_session)):
    db_user = session.exec(select(User).where(User.email == user.email)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=user.email,
        hashed_password=get_password_hash(user.password),
        is_admin=False,
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user


@app.post("/token", response_model=Token, tags=["Auth"])
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.email == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    token = jwt.encode(
        {"sub": user.email, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM
    )
    return Token(access_token=token, token_type="bearer")


@app.post("/applications/", response_model=VisaApplicationRead, tags=["Applicant"])
def create_application(
    application: VisaApplicationCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    db_application = VisaApplication.model_validate(application)
    if current_user.id is None:
        raise HTTPException(status_code=500, detail="User ID is missing")

    db_application.user_id = current_user.id

    session.add(db_application)
    session.commit()
    session.refresh(db_application)
    return db_application


@app.get(
    "/applications/me", response_model=list[VisaApplicationRead], tags=["Applicant"]
)
def read_my_applications(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return session.exec(
        select(VisaApplication).where(VisaApplication.user_id == current_user.id)
    ).all()


@app.get(
    "/admin/applications", response_model=list[VisaApplicationRead], tags=["Admin"]
)
def read_all_applications(
    session: Session = Depends(get_session), admin_user: User = Depends(get_admin_user)
):
    return session.exec(select(VisaApplication)).all()


@app.put(
    "/admin/applications/{app_id}/status",
    response_model=VisaApplicationRead,
    tags=["Admin"],
)
def update_application_status(
    app_id: int,
    status: StatusEnum,
    session: Session = Depends(get_session),
    admin_user: User = Depends(get_admin_user),
):
    application = session.get(VisaApplication, app_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    application.status = status
    session.add(application)
    session.commit()
    session.refresh(application)
    return application
