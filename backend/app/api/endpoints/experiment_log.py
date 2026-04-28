from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from app.api.dependencies import AuthUser, CurrentUser, DbSession, Permission

from app.models.experiment_log import ExperimentLog, ExperimentLogCreate, ExperimentLogLatestDevice, ExperimentLogPublic
from app.models.utils import now


router = APIRouter()


@router.get("/")
def get_all(db: DbSession, _: AuthUser = Permission("olm.experiment_log.read_all")): 
    stmt = select(ExperimentLog)
    return db.exec(stmt).all()


@router.get("/{experiment_id}/latest", response_model=ExperimentLogLatestDevice)
def get_latest_device_by_experiment(db: DbSession, experiment_id: int, user: CurrentUser):
    stmt = (
        select(ExperimentLog)
        .where(ExperimentLog.experiment_id == experiment_id)
        .where(ExperimentLog.user_id == user.id)
        .where(ExperimentLog.started_at.is_not(None))
        .order_by(ExperimentLog.started_at.desc(), ExperimentLog.id.desc())
        .limit(1)
    )
    log = db.exec(stmt).first()
    return ExperimentLogLatestDevice(device_id=log.device_id if log else None)


@router.get("/user/{user_id}", response_model=list[ExperimentLogPublic])
def get_all_by_user(db: DbSession, user_id: int):
    stmt = select(ExperimentLog).where(ExperimentLog.user_id == user_id)
    return db.exec(stmt).all()


@router.get("/{id}", response_model=ExperimentLogPublic)
def get_by_id(db: DbSession, id: int): 
    db_exp_log = db.get(ExperimentLog, id)
    if not db_exp_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Experiment Log with {id} not found!")
    return db_exp_log


def create(db: DbSession, reserved_experiment: ExperimentLogCreate, user: CurrentUser):
    db_exp_log = ExperimentLog.model_validate(reserved_experiment)
    db_exp_log.user_id = user.id
    db.add(db_exp_log)
    db.commit()
    db.refresh(db_exp_log)
    return db_exp_log


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(db: DbSession, id: int):
    db_exp_log = db.get(ExperimentLog, id)
    if not db_exp_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Experiment Log with {id} not found!")
    if db_exp_log.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_410_GONE,detail="Experiment Log already deleted")
    db_exp_log.deleted_at = now()
    db.add(db_exp_log)
    db.commit()
    db.refresh(db_exp_log)
    return None