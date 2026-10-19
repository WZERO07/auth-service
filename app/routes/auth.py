from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import RefreshToken, User
from ..schemas import RefreshRequest, Token, UserCreate, UserLogin, UserResponse
from ..security import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_password,
    hash_token,
    verify_password,
)

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)): #noqa: B008

    # Check if the user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    # Create a new user instance
    new_user = User(
        email=user.email,
        hashed_password=hash_password(user.password)
    )

    # Add the new user to the database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
def login_user(user: UserLogin, db: Session = Depends(get_db)): #noqa: B008

    # check if the user exists
    existing_user = db.query(User).filter(User.email == user.email).first()

    #if the user does not exist or the password is incorrect, raise an HTTPException with a 401
    if not existing_user or not verify_password(user.password, existing_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    # Create an access/refresh token and return the token in the response
    access_token = create_access_token({"sub": str(existing_user.id)})
    refresh_token = create_refresh_token(db, existing_user.id)
    
    return Token(access_token=access_token, token_type="bearer", refresh_token=refresh_token)


@router.post("/refresh", response_model=Token, status_code=status.HTTP_200_OK)
def refresh_token(refresh_request: RefreshRequest, db: Session = Depends(get_db)): #noqa: B008

    generated_hashed_token = hash_token(refresh_request.refresh_token)
    stored_token = db.query(RefreshToken).filter(RefreshToken.hashed_token == generated_hashed_token).first()


    if not stored_token or stored_token.revoked or stored_token.expires_at.replace(tzinfo=None) < datetime.now(timezone.utc).replace(tzinfo=None): #maiking sure to compare naive datetime objects
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")


    db.query(RefreshToken).filter(RefreshToken.id == stored_token.id).update({"revoked": True})
    db.commit()

    # Create a new access and refresh token and return it in the response
    access_token = create_access_token({"sub": str(stored_token.user_id)})
    new_refresh_token = create_refresh_token(db, stored_token.user_id)
    
    return Token(access_token=access_token, token_type="bearer", refresh_token=new_refresh_token)


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)): #noqa: B008
    return current_user