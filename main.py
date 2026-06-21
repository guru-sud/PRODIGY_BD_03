from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

import models
import schemas
import crud
from database import engine, get_db
from auth_utils import verify_password, create_access_token
from dependencies import get_current_user, require_role

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="JWT Auth API")


@app.post("/register", response_model=schemas.UserResponse, status_code=201)
def register(user: schemas.UserRegister, db: Session = Depends(get_db)):
    try:
        return crud.create_user(db, user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")


@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"sub": user.id})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/profile", response_model=schemas.UserResponse)
def get_profile(current_user: models.User = Depends(get_current_user)):
    return current_user


@app.get("/users", response_model=list[schemas.UserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("admin", "owner")),
):
    return crud.get_all_users(db)


@app.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("owner")),
):
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return None