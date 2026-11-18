from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import Base, get_db
from app.errors import NotFoundError

DbSession = Annotated[Session, Depends(get_db)]


def get_or_404[M: Base](db: Session, model: type[M], obj_id: int) -> M:
    obj = db.get(model, obj_id)
    if obj is None:
        raise NotFoundError(f"{model.__name__.lower()} {obj_id} not found")
    return obj
