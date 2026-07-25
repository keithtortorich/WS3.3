from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel


class ExecutionNodeCreate(BaseModel):
    node_type: str
    display_name: Optional[str] = None
    ref_type: Optional[str] = None
    ref_id: Optional[uuid.UUID] = None
    payload: Optional[str] = None


class ExecutionNodeRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    workflow_instance_id: uuid.UUID
    parent_node_id: Optional[uuid.UUID]
    node_type: str
    status: str
    ref_id: Optional[uuid.UUID]
    ref_type: Optional[str]
    failure_reason: Optional[str]
    completed_at: Optional[str]
    display_name: Optional[str]


class ExecutionNodeTransition(BaseModel):
    status: str
