"""seed_test_data

Revision ID: 4dbc1fd65d1c
Revises: b0a0a3429377
Create Date: 2026-03-01 20:27:35.260488

"""
from datetime import datetime
import json
from typing import Sequence, Union

import sqlmodel
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4dbc1fd65d1c'
down_revision: Union[str, Sequence[str], None] = 'b0a0a3429377'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_SOFTWARE = [
    {
        "id": 1,
        "name": "openloop",
        
    },
    {
        "id": 2,
        "name": "matlab",
    }
]
DEFAULT_DEVICETYPE = [
    {
        "id": 1,
        "name": "Arduino"
    }
]
DEFAULT_SCHEMA = [
    {
        "id": 1,
        "name": "IoT Schema",
        "note": "Main IoT device schema",
        "software_id": 2,
        "device_type_id": 1,
    }
]
DEFAULT_ARGUMENTS = [
    {
        "id": 1,
        "name": "fan_voltage",
        "label": "Fan Voltage",
        "default_value": "5.0",
        "row": 1,
        "order": 1,
        "schema_id": 1
    },
    {
        "id": 2,
        "name": "sampling_mode",
        "label": "Sampling Mode",
        "default_value": "continuous",
        "row": 2,
        "order": 2,
        "schema_id": 1
    }
]
DEFAULT_OPTIONS = [
    {
        "id": 1,
        "name": "voltage_low",
        "value": "3.3V",
        "output_value": "3.3",
        "argument_id": 1
    },
    {
        "id": 2,
        "name": "voltage_medium",
        "value": "5.0V",
        "output_value": "5.0",
        "argument_id": 1
    }
]
DEFAULT_SERVER = [
    {
        "id": 1,
        "name": "Main Server",
        "ip_address": "1127.0.0.1",
        "api_domain": "api.example.com",
        "websocket_port": 8001,
        "available": False,
        "production": False,
        "enabled": False
    }
]
DEFAULT_DEVICE = [
    {
        "id": 1,
        "name": "tom1a",
        "device_type_id": 1,
        "server_id": 1
    }
]
DEFAULT_DEVICESOFTWARE = [
    {
        "id":1,
        "device_id":1,
        "software_id":1
    },
    {
        "id":2,
        "device_id":1,
        "software_id":2,
    }
]
DEFAULT_EXPERIMENT = [
    {
        "id": 1,
        "commands": {"init": "expression","start": "expression","change": "expression","stop": "expression"},
        "experiment_commands": {
            "fan_voltage": {
                "value": 0,
                "type": "number",
                "unit": "V"
            }
        },
        "output_arguments": {"format": "json"},
        "has_schema": False,
        "server_id": 1,
        "device_type_id": 1,
        "device_id": 1,
        "software_id": 1
    },
    {
        "id": 2,
        "commands": {"init": "expression","start": "expression","change": "expression","stop": "expression"},
        "experiment_commands": {
            "fan_voltage": {
                "value": 0,
                "type": "number",
                "unit": "V"
            }
        },
        "output_arguments": {"format": "json"},
        "has_schema": True,
        "server_id": 1,
        "device_type_id": 1,
        "device_id": 1,
        "software_id": 2
    }
]

def upgrade() -> None:
    now = datetime.now()
    
    for provider in DEFAULT_SOFTWARE:
        op.execute(
            sa.text(
                """
                INSERT INTO software (id, name, created_at, modified_at)
                VALUES (:id, :name, :created_at, :modified_at)
                """
            ).bindparams(
                sa.bindparam("id", value=provider["id"]),
                sa.bindparam("name", value=provider["name"]),
                sa.bindparam("created_at", value=now),
                sa.bindparam("modified_at", value=now),
            )
        )
    for provider in DEFAULT_DEVICETYPE:
        op.execute(
            sa.text(
                """
                INSERT INTO device_type (id, name, created_at, modified_at)
                VALUES (:id, :name, :created_at, :modified_at)
                """
            ).bindparams(
                sa.bindparam("id", value=provider["id"]),
                sa.bindparam("name", value=provider["name"]),
                sa.bindparam("created_at", value=now),
                sa.bindparam("modified_at", value=now),
            )
        )
    for provider in DEFAULT_SCHEMA:
        op.execute(
            sa.text(
                """
                INSERT INTO schema (id, name, note, schema_type, software_id, device_type_id, created_at, modified_at)
                VALUES (:id, :name, :note, :schema_type, :software_id, :device_type_id, :created_at, :modified_at)
                """
            ).bindparams(
                sa.bindparam("id", value=provider["id"]),
                sa.bindparam("name", value=provider["name"]),
                sa.bindparam("note", value=provider["note"]),
                sa.bindparam("schema_type", value=provider.get("schema_type", "control")),
                sa.bindparam("software_id", value=provider["software_id"]),
                sa.bindparam("device_type_id", value=provider["device_type_id"]),
                sa.bindparam("created_at", value=now),
                sa.bindparam("modified_at", value=now),
            )
        )
    for provider in DEFAULT_ARGUMENTS:
        op.execute(
            sa.text(
                """
                INSERT INTO argument (id, name, label, default_value, row, "order", schema_id, created_at, modified_at)
                VALUES (:id, :name, :label, :default_value, :row, :order, :schema_id, :created_at, :modified_at)
                """
            ).bindparams(
                sa.bindparam("id", value=provider["id"]),
                sa.bindparam("name", value=provider["name"]),
                sa.bindparam("label", value=provider["label"]),
                sa.bindparam("default_value", value=provider["default_value"]),
                sa.bindparam("row", value=provider["row"]),
                sa.bindparam("order", value=provider["order"]),
                sa.bindparam("schema_id", value=provider["schema_id"]),
                sa.bindparam("created_at", value=now),
                sa.bindparam("modified_at", value=now),
            )
        )
    for provider in DEFAULT_OPTIONS:
        op.execute(
            sa.text(
                """
                INSERT INTO option (id, name, value, output_value, argument_id, created_at, modified_at)
                VALUES (:id, :name, :value, :output_value, :argument_id, :created_at, :modified_at)
                """
            ).bindparams(
                sa.bindparam("id", value=provider["id"]),
                sa.bindparam("name", value=provider["name"]),
                sa.bindparam("value", value=provider["value"]),
                sa.bindparam("output_value", value=provider["output_value"]),
                sa.bindparam("argument_id", value=provider["argument_id"]),
                sa.bindparam("created_at", value=now),
                sa.bindparam("modified_at", value=now),
            )
        )
    for provider in DEFAULT_SERVER:
        op.execute(
            sa.text(
                """
                INSERT INTO server (id, name, ip_address, api_domain, websocket_port, available, production, enabled, created_at, modified_at)
                VALUES (:id, :name, :ip_address, :api_domain, :websocket_port, :available, :production, :enabled, :created_at, :modified_at)
                """
            ).bindparams(
                sa.bindparam("id", value=provider["id"]),
                sa.bindparam("name", value=provider["name"]),
                sa.bindparam("ip_address", value=provider["ip_address"]),
                sa.bindparam("api_domain", value=provider["api_domain"]),
                sa.bindparam("websocket_port", value=provider["websocket_port"]),
                sa.bindparam("available", value=provider["available"]),
                sa.bindparam("production", value=provider["production"]),
                sa.bindparam("enabled", value=provider["enabled"]),
                sa.bindparam("created_at", value=now),
                sa.bindparam("modified_at", value=now),
            )
        )
    for provider in DEFAULT_DEVICE:
        op.execute(
            sa.text(
                """
                INSERT INTO device (id, name, device_type_id, server_id, created_at, modified_at)
                VALUES (:id, :name, :device_type_id, :server_id, :created_at, :modified_at)
                """
            ).bindparams(
                sa.bindparam("id", value=provider["id"]),
                sa.bindparam("name", value=provider["name"]),
                sa.bindparam("device_type_id", value=provider["device_type_id"]),
                sa.bindparam("server_id", value=provider["server_id"]),
                sa.bindparam("created_at", value=now),
                sa.bindparam("modified_at", value=now),
            )
        )
    for provider in DEFAULT_DEVICESOFTWARE:
        op.execute(
            sa.text(
                """
                INSERT INTO device_software (device_id, software_id)
                VALUES (:device_id, :software_id)
                """
            ).bindparams(
                sa.bindparam("device_id", value=provider["device_id"]),
                sa.bindparam("software_id", value=provider["software_id"]),
            )
        )
    for provider in DEFAULT_EXPERIMENT:
        op.execute(
            sa.text(
                """
                INSERT INTO experiment (id, commands, experiment_commands, output_arguments, has_schema, server_id, device_type_id, device_id, software_id, created_at, modified_at)
                VALUES (:id, :commands, :experiment_commands, :output_arguments, :has_schema, :server_id, :device_type_id, :device_id, :software_id, :created_at, :modified_at)
                """
            ).bindparams(
                sa.bindparam("id", value=provider["id"]),
                sa.bindparam("commands", value=provider["commands"], type_=sa.JSON),
                sa.bindparam("experiment_commands", value=provider["experiment_commands"], type_=sa.JSON),
                sa.bindparam("output_arguments", value=provider["output_arguments"], type_=sa.JSON),
                sa.bindparam("has_schema", value=provider["has_schema"]),
                sa.bindparam("server_id", value=provider["server_id"]),
                sa.bindparam("device_type_id", value=provider["device_type_id"]),
                sa.bindparam("device_id", value=provider["device_id"]),
                sa.bindparam("software_id", value=provider["software_id"]),
                sa.bindparam("created_at", value=now),
                sa.bindparam("modified_at", value=now),
            )
        )

def downgrade() -> None:
    for provider in DEFAULT_EXPERIMENT:
        op.execute(
            sa.text(
                """
                DELETE FROM experiment WHERE id = :id
                """
            ).bindparams(id=provider["id"])
        )
    for provider in DEFAULT_DEVICESOFTWARE:
        op.execute(
            sa.text(
                """
                DELETE FROM device_software WHERE device_id = :device_id AND software_id = :software_id
                """
            ).bindparams(device_id=provider["device_id"], software_id=provider["software_id"])
        )
    for provider in DEFAULT_DEVICE:
        op.execute(
            sa.text(
                """
                DELETE FROM device WHERE id = :id
                """
            ).bindparams(id=provider["id"])
        )
    for provider in DEFAULT_SERVER:
        op.execute(
            sa.text(
                """
                DELETE FROM server WHERE id = :id
                """
            ).bindparams(id=provider["id"])
        )
    for provider in DEFAULT_OPTIONS:
        op.execute(
            sa.text(
                """
                DELETE FROM option WHERE id = :id
                """
            ).bindparams(id=provider["id"])
        )
    for provider in DEFAULT_ARGUMENTS:
        op.execute(
            sa.text(
                """
                DELETE FROM argument WHERE id = :id
                """
            ).bindparams(id=provider["id"])
        )
    for provider in DEFAULT_SCHEMA:
        op.execute(
            sa.text(
                """
                DELETE FROM schema WHERE id = :id
                """
            ).bindparams(id=provider["id"])
        )
    for provider in DEFAULT_DEVICETYPE:
        op.execute(
            sa.text(
                """
                DELETE FROM device_type WHERE name = :name
                """
            ).bindparams(name=provider["name"])
        )
    for provider in DEFAULT_SOFTWARE:
        op.execute(
            sa.text(
                """
                DELETE FROM software WHERE name = :name
                """
            ).bindparams(name=provider["name"])
        )