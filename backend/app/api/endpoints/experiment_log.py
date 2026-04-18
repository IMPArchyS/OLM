from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from app.api.dependencies import CurrentUserId, DbSession

from app.models.experiment_log import ExperimentLog, ExperimentLogCreate, ExperimentLogPublic
from app.models.utils import now


router = APIRouter()


@router.get("/")
def get_all(db: DbSession): 
    stmt = select(ExperimentLog)
    return db.exec(stmt).all()


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


def create(db: DbSession, reserved_experiment: ExperimentLogCreate, user_id: CurrentUserId):
    db_exp_log = ExperimentLog.model_validate(reserved_experiment)
    db_exp_log.user_id = user_id
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


# @router.patch("/{id}", response_model=ExperimentLogUpdate)
# def update(db: DbSession, id: int, reserved_experiment: ExperimentLogUpdate):
#     db_reserved_exp = db.get(ExperimentLog, id)
#     if not db_reserved_exp:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reserved Experiment with {id} not found!")
#     reserved_exp_data = reserved_experiment.model_dump(exclude_unset=True)
#     db_reserved_exp.sqlmodel_update(reserved_exp_data)
    
#     if not db.get(Experiment, reserved_experiment.experiment_id):
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Experiment with {reserved_experiment.experiment_id} not found!")
    
#     if not db.get(Device, reserved_experiment.device_id):
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device with {reserved_experiment.device_id} not found!")    
    
#     if not db.get(Schema, reserved_experiment.schema_id):
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Schema with {reserved_experiment.schema_id} not found!")    
    
#     db.add(db_reserved_exp)
#     db.commit()
#     db.refresh(db_reserved_exp)
#     return db_reserved_exp
