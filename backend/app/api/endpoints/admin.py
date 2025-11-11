from fastapi import APIRouter
from sqlmodel import delete, select
from app.api.dependencies import DbSession

from app.models.device import Device
from app.models.device_type import DeviceType, DeviceTypeCreate
from app.models.device_software import DeviceSoftware
from app.models.reservation import Reservation
from app.models.software import Software
from app.models.experiment import Experiment
from app.models.reserved_experiment import ReservedExperiment
from app.models.schema import Schema
from app.models.server import Server
from app.models.utils import now


router = APIRouter()


@router.get("/time")
def time():
    return now()


@router.post("/seed")
def seed(db: DbSession):
    # 1. Create Software first (needed by Schema)    
    software = Software(
        name="Matlab"
    )
    db.add(software)
    db.commit()
    db.refresh(software)
    
    # 2. Create Schema (depends on Software)
    if software.id is None:
        raise ValueError("Software ID cannot be None")
        
    schema = Schema(
        name="IoT Schema",
        note="Main IoT device schema",
        software_id=software.id
    )
    db.add(schema)
    db.commit()
    db.refresh(schema)
    
    # 3. Create Server (no dependencies)
    server = Server(
        name="Main Server",
        ip_address="192.168.1.100",
        api_domain="api.example.com",
        websocket_port=8080,
        available=True,
        production=False,
        enabled=True
    )
    db.add(server)
    db.commit()
    db.refresh(server)
    
    # 4. Create DeviceType (depends on Schema)
    if schema.id is None:
        raise ValueError("Schema ID cannot be None")
    
    device_type = DeviceType(
        name="Sensor",
        schema_id=schema.id
    )
    db.add(device_type)
    db.commit()
    db.refresh(device_type)
    
    # 5. Create Device (depends on DeviceType and Server)
    if device_type.id is None:
        raise ValueError("Device Type ID cannot be None")
    
    if server.id is None:
        raise ValueError("Server ID cannot be None")
    
    device = Device(
        name="tom1a",
        device_type_id=device_type.id,
        server_id=server.id
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    
    # 6. Create DeviceSoftware (many-to-many relationship)
    if device.id is None:
        raise ValueError("Device ID cannot be None")
    
    if software.id is None:
        raise ValueError("Software ID cannot be None")
    
    device_software = DeviceSoftware(
        device_id=device.id,
        software_id=software.id
    )
    db.add(device_software)
    db.commit()
    db.refresh(device_software)
    
    # 7. Create Experiment (depends on Server, DeviceType, Device, Software)
    experiment = Experiment(
        commands={"init": "expression","start": "expression","change": "expression","stop": "expression"},
        experiment_commands={
            "fan_voltage": {
                "value": 0,
                "type": "number",
                "unit": "V"
            }
        },
        output_arguments={"format": "json"},
        has_schema=True,
        server_id=server.id,
        device_type_id=device_type.id,
        device_id=device.id,
        software_id=software.id
    )
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    
    # 8. Create ReservedExperiment (depends on Experiment, Device, Schema)
    if experiment.id is None:
        raise ValueError("Experiment ID cannot be None")
    
    reserved_experiment = ReservedExperiment(
        input={"temperature_range": "20-30"},
        output={"readings": []},
        note="Test reservation",
        simulation_time=3600,
        sampling_rate=100,
        filled=False,
        experiment_id=experiment.id,
        device_id=device.id,
        schema_id=schema.id
    )
    db.add(reserved_experiment)
    db.commit()
    db.refresh(reserved_experiment)
    
    return {
        "message": "Database seeded successfully",
        "created": {
            "software_id": software.id,
            "schema_id": schema.id,
            "server_id": server.id,
            "device_type_id": device_type.id,
            "device_id": device.id,
            "experiment_id": experiment.id,
            "reserved_experiment_id": reserved_experiment.id
        }
    }
    

@router.delete("/clear")
def clear(db: DbSession):
    db.exec(delete(Reservation))
    db.exec(delete(ReservedExperiment))
    db.exec(delete(Experiment))
    db.exec(delete(DeviceSoftware))
    db.exec(delete(Device))
    db.exec(delete(DeviceType))
    db.exec(delete(Server))
    db.exec(delete(Schema))
    db.exec(delete(Software))
    db.commit()
    return {"message": "Database cleared successfully"}