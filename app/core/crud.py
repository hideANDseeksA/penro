"""Generic CRUD router factory.

Every registry/reference entity in the ERD gets the same treatment: a
paginated + server-side filtered list endpoint, a detail endpoint, and
role-gated write endpoints that leave an AUDIT_LOG trail. Entities with real
business rules (clearances, assessments, returns, remedies) get purpose-built
endpoints in `routers/operations.py` instead of relying on raw CRUD.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.core.permission import ADMIN, TAXPAYER, TREASURER_STAFF, require_roles
from app.core.security import CurrentUser, db_session, get_current_user
from app.schemas.factory import make_schemas
from app.schemas.pagination import Page, PageParams
from app.service.audit_service import record_audit
from app.utils.query_filters import paginate

WRITE_ROLES_DEFAULT = (ADMIN, TREASURER_STAFF)


def build_crud_router(
    model,
    *,
    prefix: str,
    tag: str,
    write_roles: tuple[str, ...] = WRITE_ROLES_DEFAULT,
    read_roles: tuple[str, ...] | None = None,
    allow_delete: bool = False,
    taxpayer_scoped: bool = False,
    read_only: bool = False,
) -> APIRouter:
    ReadSchema, CreateSchema, UpdateSchema = make_schemas(model)
    pk_col = list(inspect(model).primary_key)[0]
    entity = model.__tablename__
    router = APIRouter(prefix=prefix, tags=[tag])

    read_dep = Depends(require_roles(*read_roles)) if read_roles else Depends(get_current_user)
    write_dep = Depends(require_roles(*write_roles))

    def _scope(user: CurrentUser) -> list:
        """Taxpayer portal users only ever see their own rows."""
        if taxpayer_scoped and user.role == TAXPAYER and user.taxpayer_id:
            return [model.taxpayer_id == user.taxpayer_id]
        return []

    @router.get("", response_model=Page[ReadSchema], summary=f"List {entity} (paginated, filterable)")
    def list_items(
        params: PageParams = Depends(),
        db: Session = Depends(db_session),
        user: CurrentUser = read_dep,
    ) -> Any:
        return paginate(db, model, params, base_conditions=_scope(user))

    @router.get("/{item_id}", response_model=ReadSchema, summary=f"Get one {entity}")
    def get_item(
        item_id: str,
        db: Session = Depends(db_session),
        user: CurrentUser = read_dep,
    ) -> Any:
        obj = db.get(model, item_id)
        if obj is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"{entity} not found")
        for cond in _scope(user):
            if not db.query(model).filter(pk_col == item_id).filter(cond).count():
                raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your record")
        return obj

    if read_only:
        return router

    @router.post("", response_model=ReadSchema, status_code=status.HTTP_201_CREATED)
    def create_item(
        payload: CreateSchema,  # type: ignore[valid-type]
        request: Request,
        db: Session = Depends(db_session),
        user: CurrentUser = write_dep,
    ) -> Any:
        obj = model(**payload.model_dump(exclude_unset=True))
        db.add(obj)
        db.flush()
        record_audit(
            db, request=request, user_id=user.user_id, action="create",
            entity_name=entity, entity_id=getattr(obj, pk_col.key),
        )
        return obj

    @router.patch("/{item_id}", response_model=ReadSchema)
    def update_item(
        item_id: str,
        payload: UpdateSchema,  # type: ignore[valid-type]
        request: Request,
        db: Session = Depends(db_session),
        user: CurrentUser = write_dep,
    ) -> Any:
        obj = db.get(model, item_id)
        if obj is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"{entity} not found")
        changes = payload.model_dump(exclude_unset=True)
        changes.pop(pk_col.key, None)
        for key, value in changes.items():
            setattr(obj, key, value)
        db.flush()
        record_audit(
            db, request=request, user_id=user.user_id, action="update",
            entity_name=entity, entity_id=item_id, details=changes,
        )
        return obj

    if allow_delete:
        @router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
        def delete_item(
            item_id: str,
            request: Request,
            db: Session = Depends(db_session),
            user: CurrentUser = Depends(require_roles(ADMIN)),
        ) -> None:
            obj = db.get(model, item_id)
            if obj is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, f"{entity} not found")
            db.delete(obj)
            record_audit(
                db, request=request, user_id=user.user_id, action="delete",
                entity_name=entity, entity_id=item_id,
            )

    return router
