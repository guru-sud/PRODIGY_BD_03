from sqlalchemy.orm import Session
import models
import schemas
from auth_utils import hash_password


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_id(db: Session, user_id: str):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_all_users(db: Session):
    return db.query(models.User).all()


def create_user(db: Session, user: schemas.UserRegister):
    db_user = models.User(
        name=user.name,
        email=user.email,
        hashed_password=hash_password(user.password),
        role=user.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user