from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.security import hash_password, verify_password, create_access_token

router = APIRouter()

@router.post("/register")
def register(
    email: str = Form(...),
    password: str = Form(...),
    fullname: str = Form(""),
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà utilisé.")

    user = User(
        email=email,
        hashed_password=hash_password(password),
        fullname=fullname
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "Utilisateur créé", "id": user.id}


@router.post("/login")
def login(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Identifiants incorrects.")

    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}
