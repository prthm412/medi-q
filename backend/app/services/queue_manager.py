import json
import uuid
from datetime import datetime, timezone

from app.core.config import settings
from app.core.redis_client import redis_client

QUEUE_KEY_PREFIX = "queue"
CHANNEL_PREFIX = "queue_channel"


def _queue_key(doctor_id: uuid.UUID) -> str:
    return f"{QUEUE_KEY_PREFIX}:{doctor_id}"


def channel_name(doctor_id: uuid.UUID) -> str:
    return f"{CHANNEL_PREFIX}:{doctor_id}"


def get_position(doctor_id: uuid.UUID, patient_id: uuid.UUID) -> dict | None:
    """Position/wait estimate for a patient currently in the doctor's queue,
    or None if they're not in it (not checked in, or already removed)."""
    rank = redis_client.zrank(_queue_key(doctor_id), str(patient_id))
    if rank is None:
        return None
    position = rank + 1
    return {
        "position": position,
        "estimated_wait_minutes": position * settings.AVG_CONSULTATION_MINUTES,
    }


def check_in(doctor_id: uuid.UUID, patient_id: uuid.UUID) -> dict | None:
    """Add a patient to the doctor's waiting queue, scored by check-in time.
    Returns the new position, or None if they were already checked in."""
    key = _queue_key(doctor_id)
    score = datetime.now(timezone.utc).timestamp()
    added = redis_client.zadd(key, {str(patient_id): score}, nx=True)
    if not added:
        return None

    position_data = get_position(doctor_id, patient_id)
    _publish_position(doctor_id, patient_id, position_data)
    return position_data


def remove_and_rebroadcast(doctor_id: uuid.UUID, patient_id: uuid.UUID) -> None:
    """Remove a patient from the waiting queue (their appointment moved past
    'scheduled') and push fresh positions to everyone still waiting behind them."""
    key = _queue_key(doctor_id)
    redis_client.zrem(key, str(patient_id))

    remaining = redis_client.zrange(key, 0, -1)  # ascending by score = queue order
    for index, member in enumerate(remaining):
        position = index + 1
        position_data = {
            "position": position,
            "estimated_wait_minutes": position * settings.AVG_CONSULTATION_MINUTES,
        }
        _publish_position(doctor_id, uuid.UUID(member), position_data)


def _publish_position(doctor_id: uuid.UUID, patient_id: uuid.UUID, position_data: dict) -> None:
    message = {
        "type": "position_update",
        "patient_id": str(patient_id),
        **position_data,
    }
    redis_client.publish(channel_name(doctor_id), json.dumps(message))