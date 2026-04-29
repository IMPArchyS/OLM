from fastapi import APIRouter, HTTPException, status
from sqlmodel import col, select
from app.api.dependencies import AuthUser, CurrentUser, DbSession, Permission

from app.models.experiment_log import ExperimentLog, ExperimentLogCreate, ExperimentLogLatestDevice, ExperimentLogPublic, ExperimentLogPublicEnriched
from app.models.utils import now


router = APIRouter()


def _enrich(log: ExperimentLog) -> ExperimentLogPublicEnriched:
    software_name: str | None = None
    if log.experiment and log.experiment.software:
        software_name = log.experiment.software.name
    return ExperimentLogPublicEnriched(
        **ExperimentLogPublic.model_validate(log).model_dump(),
        server_name=log.server.name if log.server else None,
        device_name=log.device.name if log.device else None,
        software_name=software_name,
    )


@router.get("/", response_model=list[ExperimentLogPublicEnriched])
def get_all(db: DbSession, _: AuthUser = Permission("olm.experiment_log.read_all")):
    stmt = select(ExperimentLog)
    return [_enrich(log) for log in db.exec(stmt).all()]


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


@router.get("/user/{user_id}", response_model=list[ExperimentLogPublicEnriched])
def get_all_by_user(db: DbSession, user_id: int):
    stmt = select(ExperimentLog).where(ExperimentLog.user_id == user_id)
    return [_enrich(log) for log in db.exec(stmt).all()]


@router.get("/{id}", response_model=ExperimentLogPublicEnriched)
def get_by_id(db: DbSession, id: int):
    db_exp_log = db.get(ExperimentLog, id)
    if not db_exp_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Experiment Log with {id} not found!")
    return _enrich(db_exp_log)


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
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Experiment Log already deleted")
    db_exp_log.deleted_at = now()
    db.add(db_exp_log)
    db.commit()
    db.refresh(db_exp_log)
    return None


@router.patch("/{id}/restore", response_model=ExperimentLogPublicEnriched)
def restore(db: DbSession, id: int):
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