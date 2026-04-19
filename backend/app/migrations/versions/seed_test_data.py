"""seed_test_data

Revision ID: 11_seed_test_data
Revises: 10_create_exp_queue_tbl
Create Date: 2026-03-01 20:27:35.260488

"""
from datetime import datetime
import json
from typing import Sequence, Union

import sqlmodel
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '11_seed_test_data'
down_revision: Union[str, Sequence[str], None] = '10_create_exp_queue_tbl'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_SOFTWARE = [
    {
        "id": 1,
        "name": "openloop",
    },
]
DEFAULT_DEVICETYPE = [
    {
        "id": 1,
        "name": "sinusoid"
    }
]
DEFAULT_SERVER = [
    {
        "id": 1,
        "name": "Main",
        "ip_address": "127.0.0.1",
        "api_domain": "localhost",
        "port": 8001,
        "available": False,
        "production": False,
        "enabled": False
    }
]
DEFAULT_DEVICE = [
    {
        "id": 1,
        "name": "sinusoid 1",
        "device_type_id": 1,
        "server_id": 1
    }
]
DEFAULT_DEVICESOFTWARE = [
    {
        "id":1,
        "device_id":1,
        "software_id":1
    }
]
DEFAULT_EXPERIMENT = [
    {
        "id": 1,
        "commands": ["start", "change", "stop"], # init
        "input_arguments": {
            "sin_amplitude": {
                "value": 0,
                "type": "number",
                "unit": "Hz",
                "order": 1
            },
            "sin_frequency": {
                "value": 0,
                "type": "number",
                "unit": "Hz",
                "order": 2
            }
        },
        "output_arguments": ["sin_y"],
        "software_id": 1
    }
]
DEFAULT_EXPERIMENTDEVICE = [
    {
        "experiment_id": 1,
        "device_id": 1,
    }
]

def upgrade() -> None:
    now = datetime.now()
    
    for item in DEFAULT_SOFTWARE:
        op.execute(
            sa.text(
                """
                INSERT INTO software (id, name, created_at, modified_at)
                VALUES (:id, :name, :created_at, :modified_at)
                """
            ).bindparams(
                sa.bindparam("id", value=item["id"]),
                sa.bindparam("name", value=item["name"]),
                sa.bindparam("created_at", value=now),
                sa.bindparam("modified_at", value=now),
            )
        )
    for item in DEFAULT_DEVICETYPE:
        op.execute(
            sa.text(
                """
                INSERT INTO device_type (id, name, created_at, modified_at)
                VALUES (:id, :name, :created_at, :modified_at)
                """
            ).bindparams(
                sa.bindparam("id", value=item["id"]),
                sa.bindparam("name", value=item["name"]),
                sa.bindparam("created_at", value=now),
                sa.bindparam("modified_at", value=now),
            )
        )
    for item in DEFAULT_SERVER:
        op.execute(
            sa.text(
                """
                INSERT INTO server (id, name, ip_address, api_domain, port, available, production, enabled, created_at, modified_at)
                VALUES (:id, :name, :ip_address, :api_domain, :port, :available, :production, :enabled, :created_at, :modified_at)
                """
            ).bindparams(
                sa.bindparam("id", value=item["id"]),
                sa.bindparam("name", value=item["name"]),
                sa.bindparam("ip_address", value=item["ip_address"]),
                sa.bindparam("api_domain", value=item["api_domain"]),
                sa.bindparam("port", value=item["port"]),
                sa.bindparam("available", value=item["available"]),
                sa.bindparam("production", value=item["production"]),
                sa.bindparam("enabled", value=item["enabled"]),
                sa.bindparam("created_at", value=now),
                sa.bindparam("modified_at", value=now),
            )
        )
    for item in DEFAULT_DEVICE:
        op.execute(
            sa.text(
                """
                INSERT INTO device (id, name, device_type_id, server_id, created_at, modified_at)
                VALUES (:id, :name, :device_type_id, :server_id, :created_at, :modified_at)
                """
            ).bindparams(
                sa.bindparam("id", value=item["id"]),
                sa.bindparam("name", value=item["name"]),
                sa.bindparam("device_type_id", value=item["device_type_id"]),
                sa.bindparam("server_id", value=item["server_id"]),
                sa.bindparam("created_at", value=now),
                sa.bindparam("modified_at", value=now),
            )
        )
    for item in DEFAULT_DEVICESOFTWARE:
        op.execute(
            sa.text(
                """
                INSERT INTO device_software (device_id, software_id)
                VALUES (:device_id, :software_id)
                """
            ).bindparams(
                sa.bindparam("device_id", value=item["device_id"]),
                sa.bindparam("software_id", value=item["software_id"]),
            )
        )
    for item in DEFAULT_EXPERIMENT:
        op.execute(
            sa.text(
                """
                INSERT INTO experiment (id, commands, input_arguments, output_arguments, software_id, created_at, modified_at)
                VALUES (:id, :commands, :input_arguments, :output_arguments, :software_id, :created_at, :modified_at)
                """
            ).bindparams(
                sa.bindparam("id", value=item["id"]),
                sa.bindparam("commands", value=item["commands"], type_=postgresql.JSONB),
                sa.bindparam("input_arguments", value=item["input_arguments"], type_=postgresql.JSONB),
                sa.bindparam("output_arguments", value=item["output_arguments"], type_=postgresql.JSONB),
                sa.bindparam("software_id", value=item["software_id"]),
                sa.bindparam("created_at", value=now),
                sa.bindparam("modified_at", value=now),
            )
        )
    for item in DEFAULT_EXPERIMENTDEVICE:
        op.execute(
            sa.text(
                """
                INSERT INTO experiment_device (experiment_id, device_id)
                VALUES (:experiment_id, :device_id)
                """
            ).bindparams(
                sa.bindparam("experiment_id", value=item["experiment_id"]),
                sa.bindparam("device_id", value=item["device_id"]),
            )
        )

    op.execute(
        sa.text(
            """
            DO $$
            DECLARE
                target_table text;
                target_sequence text;
                max_id bigint;
            BEGIN
                FOREACH target_table IN ARRAY ARRAY[
                    'software',
                    'device_type',
                    'server',
                    'device',
                    'experiment'
                ]
                LOOP
                    SELECT pg_get_serial_sequence(target_table, 'id')
                    INTO target_sequence;

                    IF target_sequence IS NOT NULL THEN
                        EXECUTE format('SELECT MAX(id) FROM %I', target_table)
                        INTO max_id;

                        IF max_id IS NULL THEN
                            EXECUTE format('SELECT setval(%L, 1, false)', target_sequence);
                        ELSE
                            EXECUTE format('SELECT setval(%L, %s, true)', target_sequence, max_id);
                        END IF;
                    END IF;
                END LOOP;
            END $$;
            """
        )
    )

def downgrade() -> None:
    for item in DEFAULT_EXPERIMENT:
        op.execute(
            sa.text(
                """
                DELETE FROM experiment_queue
                WHERE experiment_id = :id
                """
            ).bindparams(id=item["id"])
        )
        op.execute(
            sa.text(
                """
                DELETE FROM experiment_log
                WHERE experiment_id = :id
                """
            ).bindparams(id=item["id"])
        )

    for item in DEFAULT_EXPERIMENTDEVICE:
        op.execute(
            sa.text(
                """
                DELETE FROM experiment_device
                WHERE experiment_id = :experiment_id AND device_id = :device_id
                """
            ).bindparams(experiment_id=item["experiment_id"], device_id=item["device_id"])
        )
    for item in DEFAULT_EXPERIMENT:
        op.execute(
            sa.text(
                """
                DELETE FROM experiment WHERE id = :id
                """
            ).bindparams(id=item["id"])
        )
    for item in DEFAULT_DEVICESOFTWARE:
        op.execute(
            sa.text(
                """
                DELETE FROM device_software WHERE device_id = :device_id AND software_id = :software_id
                """
            ).bindparams(device_id=item["device_id"], software_id=item["software_id"])
        )
    for item in DEFAULT_DEVICE:
        op.execute(
            sa.text(
                """
                DELETE FROM reservation
                WHERE device_id = :id
                """
            ).bindparams(id=item["id"])
        )
        op.execute(
            sa.text(
                """
                DELETE FROM experiment_queue
                WHERE device_id = :id
                """
            ).bindparams(id=item["id"])
        )
        op.execute(
            sa.text(
                """
                DELETE FROM experiment_log
                WHERE device_id = :id
                """
            ).bindparams(id=item["id"])
        )
        op.execute(
            sa.text(
                """
                DELETE FROM device WHERE id = :id
                """
            ).bindparams(id=item["id"])
        )
    for item in DEFAULT_SERVER:
        op.execute(
            sa.text(
                """
                DELETE FROM experiment_device
                WHERE device_id IN (
                    SELECT id
                    FROM device
                    WHERE server_id = :id
                )
                """
            ).bindparams(id=item["id"])
        )
        op.execute(
            sa.text(
                """
                DELETE FROM device_software
                WHERE device_id IN (
                    SELECT id
                    FROM device
                    WHERE server_id = :id
                )
                """
            ).bindparams(id=item["id"])
        )
        op.execute(
            sa.text(
                """
                DELETE FROM reservation
                WHERE device_id IN (
                    SELECT id
                    FROM device
                    WHERE server_id = :id
                )
                """
            ).bindparams(id=item["id"])
        )
        op.execute(
            sa.text(
                """
                DELETE FROM experiment_queue
                WHERE device_id IN (
                    SELECT id
                    FROM device
                    WHERE server_id = :id
                )
                """
            ).bindparams(id=item["id"])
        )
        op.execute(
            sa.text(
                """
                DELETE FROM experiment_log
                WHERE device_id IN (
                    SELECT id
                    FROM device
                    WHERE server_id = :id
                )
                """
            ).bindparams(id=item["id"])
        )
        op.execute(
            sa.text(
                """
                DELETE FROM device
                WHERE server_id = :id
                """
            ).bindparams(id=item["id"])
        )
        op.execute(
            sa.text(
                """
                DELETE FROM experiment_queue
                WHERE server_id = :id
                """
            ).bindparams(id=item["id"])
        )
        op.execute(
            sa.text(
                """
                DELETE FROM experiment_log
                WHERE server_id = :id
                """
            ).bindparams(id=item["id"])
        )
        op.execute(
            sa.text(
                """
                DELETE FROM server WHERE id = :id
                """
            ).bindparams(id=item["id"])
        )
    for item in DEFAULT_DEVICETYPE:
        op.execute(
            sa.text(
                """
                DELETE FROM device_type WHERE name = :name
                """
            ).bindparams(name=item["name"])
        )
    for item in DEFAULT_SOFTWARE:
        op.execute(
            sa.text(
                """
                DELETE FROM software WHERE name = :name
                """
            ).bindparams(name=item["name"])
        )