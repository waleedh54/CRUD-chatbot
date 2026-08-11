from sqlalchemy.orm import Session
import models


class UserAlreadyExistsError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


def get_admin_by_email(db: Session, email: str):
    return db.query(models.Admin).filter(models.Admin.email == email.lower()).first()


def create_admin_if_not_exists(db: Session, email: str, name: str = None):
    admin = get_admin_by_email(db, email)
    if admin:
        return admin
    admin = models.Admin(email=email.lower(), name=name)
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def find_user(db: Session, identifier: str):
    if not identifier:
        return None
    identifier = identifier.strip()
    user = db.query(models.User).filter(models.User.email == identifier.lower()).first()
    if user:
        return user
    return db.query(models.User).filter(models.User.name.ilike(f"%{identifier}%")).first()


def create_user(db: Session, email: str, fields: dict):
    """Registers a new user record. Raises if the email is already taken."""
    existing = db.query(models.User).filter(models.User.email == email.lower()).first()
    if existing:
        raise UserAlreadyExistsError(email)

    user = models.User(
        email=email.lower(),
        name=fields.get("name"),
        phone=fields.get("phone"),
        city=fields.get("city"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, identifier: str):
    user = find_user(db, identifier)
    if not user:
        raise UserNotFoundError(identifier)
    db.delete(user)
    db.commit()
    return True


def update_user(db: Session, identifier: str, fields: dict):
    user = find_user(db, identifier)
    if not user:
        raise UserNotFoundError(identifier)
    for key, value in fields.items():
        if hasattr(user, key) and key != "id":
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session):
    return db.query(models.User).all()