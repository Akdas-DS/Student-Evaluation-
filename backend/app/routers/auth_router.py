from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/signup", response_model=schemas.TokenResponse)
def signup(data: schemas.UserSignup, db: Session = Depends(get_db)):
    if data.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public signup is only available for students. Admins must create teacher/admin accounts.",
        )

    if db.query(models.User).filter(models.User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    if data.student_id:
        if db.query(models.User).filter(models.User.student_id == data.student_id).first():
            raise HTTPException(status_code=400, detail="Student ID already in use")

    user = models.User(
        name=data.name,
        email=data.email,
        password_hash=auth.hash_password(data.password),
        role=data.role,
        student_id=data.student_id,
        department=data.department,
        semester=data.semester,
        field_id=data.field_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = auth.create_access_token({"sub": str(user.id)})
    return schemas.TokenResponse(
        access_token=token,
        user=schemas.UserOut.model_validate(user),
    )


@router.post("/login", response_model=schemas.TokenResponse)
def login(data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user or not auth.verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = auth.create_access_token({"sub": str(user.id)})
    return schemas.TokenResponse(
        access_token=token,
        user=schemas.UserOut.model_validate(user),
    )


@router.get("/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    return schemas.UserOut.model_validate(current_user)


@router.post("/reset-password")
def reset_password(data: schemas.PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.password_hash = auth.hash_password(data.new_password)
    db.commit()
    
    return {"detail": "Password successfully reset"}
