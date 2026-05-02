import asyncio
from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import selectinload
from sqlmodel import col, select
from app.api.dependencies import AuthUser, CurrentUser, DbSession, Permission, fetch_username

from app.models.experiment import Experiment
from app.models.experiment_log import ExperimentLog, ExperimentLogLatestDevice, ExperimentLogPublic, ExperimentLogPublicEnriched
from app.models.utils import now


router = APIRouter()


def _enrich(log: ExperimentLog, username: str | None = None) -> ExperimentLogPublicEnriched:
    software_name: str | None = None
    if log.experiment and log.experiment.software:
        software_name = log.experiment.software.name
    return ExperimentLogPublicEnriched(
        **ExperimentLogPublic.model_validate(log).model_dump(),
        server_name=log.server.name if log.server else None,
        device_name=log.device.name if log.device else None,
        software_name=software_name,
        username=username,
    )


def _logs_query():
    return select(ExperimentLog).options(
        selectinload(ExperimentLog.experiment).selectinload(Experiment.software),  # type: ignore[arg-type]
        selectinload(ExperimentLog.server),  # type: ignore[arg-type]
        selectinload(ExperimentLog.device),  # type: ignore[arg-type]
    )


@router.get("/", response_model=list[ExperimentLogPublicEnriched])
async def get_all(db: DbSession, _: AuthUser = Permission("olm.experiment_log.read_all")):
    logs = db.exec(_logs_query()).all()
    unique_user_ids = list({log.user_id for log in logs})
    user_map: dict[int, str] = {}
    if unique_user_ids:
        results = await asyncio.gather(*[fetch_username(uid) for uid in unique_user_ids])
        user_map = dict(results)
    return [_enrich(log, username=user_map.get(log.user_id)) for log in logs]


@router.get("/{experiment_id}/latest", response_model=ExperimentLogLatestDevice)
def get_latest_device_by_experiment(db: DbSession, experiment_id: int, user: CurrentUser):
    stmt = (
        select(ExperimentLog)
        .where(ExperimentLog.experiment_id == experiment_id)
        .where(ExperimentLog.user_id == user.id)
        .where(col(ExperimentLog.started_at).is_not(None))
        .order_by(col(ExperimentLog.started_at).desc(), col(ExperimentLog.id).desc())
        .limit(1)
    )
    log = db.exec(stmt).first()
    return ExperimentLogLatestDevice(device_id=log.device_id if log else None)


@router.get("/me", response_model=list[ExperimentLogPublicEnriched])
async def get_all_by_user(db: DbSession, user: CurrentUser):
    logs = db.exec(_logs_query().where(col(ExperimentLog.user_id) == user.id)).all()
    username: str | None = None
    if logs:
        _, username = await fetch_username(user.id)
    return [_enrich(log, username=username) for log in logs]


@router.get("/{id}", response_model=ExperimentLogPublicEnriched)
def get_by_id(db: DbSession, id: int, _: CurrentUser):
    db_exp_log = db.get(ExperimentLog, id)
    if not db_exp_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Experiment Log with {id} not found!")
    return _enrich(db_exp_log)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(db: DbSession, id: int, _: CurrentUser):
    db_exp_log = db.get(ExperimentLog, id)
    if not db_exp_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Experiment Log with {id} not found!")
    if db_exp_log.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Experiment Log already deleted")
    db_exp_log.deleted_at = now()
    db.add(db_exp_log)
    db.commit()
    db.refresh(db_exp_log)
    return None


@router.patch("/{id}/restore", response_model=ExperimentLogPublicEnriched)
def restore(db: DbSession, id: int, _: CurrentUser):
    db_exp_log = db.get(ExperimentLog, id)
    if not db_exp_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Experiment Log with {id} not found!")
    if db_exp_log.deleted_at is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Experiment Log is not deleted")
    db_exp_log.deleted_at = None
    db.add(db_exp_log)
    db.commit()
    db.refresh(db_exp_log)
    return _enrich(db_exp_log)