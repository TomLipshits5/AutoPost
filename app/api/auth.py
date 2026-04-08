import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    UserRegister, UserLogin, UserResponse, UserWithApiKey,
    TikTokTokenCreate, TikTokCredentialResponse
)
from app.models import User, TikTokCredential
from app.security import (
    hash_password, verify_password, create_api_key, get_current_user
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.post("/register", response_model=UserWithApiKey)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    api_key = create_api_key()
    user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        api_key=api_key
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(f"New user registered: {user.email}")

    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at,
        "api_key": api_key
    }


@router.post("/login", response_model=UserWithApiKey)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user and return API key"""
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at,
        "api_key": user.api_key
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "created_at": current_user.created_at
    }


@router.post("/tiktok/token", response_model=TikTokCredentialResponse)
async def add_tiktok_token(
    token_data: TikTokTokenCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Store manual TikTok access token"""
    # Check if credential already exists
    existing_cred = db.query(TikTokCredential).filter(
        TikTokCredential.user_id == current_user.id,
        TikTokCredential.open_id == token_data.open_id
    ).first()

    if existing_cred:
        # Update existing credential
        existing_cred.access_token = token_data.access_token
        existing_cred.refresh_token = token_data.refresh_token
        existing_cred.is_active = 1
        db.commit()
        db.refresh(existing_cred)
        logger.info(f"TikTok credential updated for user {current_user.email}")
        credential = existing_cred
    else:
        # Create new credential
        credential = TikTokCredential(
            user_id=current_user.id,
            access_token=token_data.access_token,
            open_id=token_data.open_id,
            refresh_token=token_data.refresh_token,
            is_active=1
        )
        db.add(credential)
        db.commit()
        db.refresh(credential)
        logger.info(f"New TikTok credential added for user {current_user.email}")

    return {
        "id": credential.id,
        "open_id": credential.open_id,
        "is_active": bool(credential.is_active),
        "created_at": credential.created_at
    }


@router.get("/tiktok/credentials", response_model=list[TikTokCredentialResponse])
async def list_tiktok_credentials(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all TikTok credentials for current user"""
    credentials = db.query(TikTokCredential).filter(
        TikTokCredential.user_id == current_user.id
    ).all()

    return [
        {
            "id": cred.id,
            "open_id": cred.open_id,
            "is_active": bool(cred.is_active),
            "created_at": cred.created_at
        }
        for cred in credentials
    ]


@router.get("/tiktok/oauth-url")
async def get_oauth_url():
    """
    Get TikTok OAuth redirect URL.
    User should redirect to this URL to authorize the app.
    """
    from app.config import get_settings
    settings = get_settings()

    oauth_url = (
        f"https://www.tiktok.com/v3/auth/oauth/authorize?"
        f"client_key={settings.tiktok_client_key}"
        f"&response_type=code"
        f"&scope=video.upload"
        f"&redirect_uri={settings.tiktok_oauth_redirect_uri}"
    )

    return {"oauth_url": oauth_url}


@router.get("/tiktok/callback")
async def tiktok_oauth_callback(code: str = None, db: Session = Depends(get_db)):
    """
    Handle TikTok OAuth callback.
    Note: This is a simplified implementation. In production, you should:
    1. Use the code to get access token from TikTok backend
    2. Link token to user (requires storing state or session info)
    3. Return JWT or redirect to frontend with credentials
    """
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code not provided"
        )

    # TODO: Exchange code for access token with TikTok backend
    # This requires making a server-to-server request with client_secret
    # For now, return instructions

    return {
        "message": "OAuth callback received successfully",
        "code": code,
        "next_steps": "Exchange this code for access token using TikTok API, then call POST /api/auth/tiktok/token with the access token"
    }
