from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User
from ..schemas.auth import LoginRequest, TokenResponse, UserOut
from ..services.audit import log_audit
from .security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.strip().lower()).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled")
    token = create_access_token(user.id, user.role)
    log_audit(db, "login", "user", entity_id=user.id, actor=user, after={"role": user.role})
    db.commit()
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))