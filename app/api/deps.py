from typing import Annotated, TypeVar

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import Base, get_db
from app.errors import NotFound

DbSession = Annotated[Session, Depends(get_db)]

M = TypeVar("M", bound=Base)


def get_or_404(db: Session, model: type[M], obj_id: int) -> M:
    obj = db.get(model, obj_id)
    if obj is None:
        raise NotFound(f"{model.__name__.lower()} {obj_id} not found")
    return obj
