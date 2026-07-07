"""
Pydantic models for the Isometric -> MTO pipeline.

These mirror the JSON contract in the assessment brief (Section 3.4):
drawing metadata, a flat list of MTO line items, and a server-computed
summary block.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Category(str, Enum):
    PIPE = "PIPE"
    FITTING = "FITTING"
    FLANGE = "FLANGE"
    VALVE = "VALVE"
    GASKET = "GASKET"
    BOLT = "BOLT"
    SUPPORT = "SUPPORT"
    OTHER = "OTHER"


class DrawingMeta(BaseModel):
    drawing_no: Optional[str] = None
    revision: Optional[str] = None
    line_number: Optional[str] = None
    nps: Optional[str] = None
    material_class: Optional[str] = None
    service: Optional[str] = None
    thumbnail_base64: Optional[str] = None


class MTOItem(BaseModel):
    item_no: int
    category: Category
    description: str
    size_nps: Optional[str] = None
    schedule_rating: Optional[str] = None
    material_spec: Optional[str] = None
    end_type: Optional[str] = None
    quantity: float = Field(ge=0)
    unit: str = "EA"
    length_m: Optional[float] = Field(default=None, ge=0)
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    remarks: Optional[str] = ""

    @field_validator("unit")
    @classmethod
    def unit_upper(cls, v: str) -> str:
        return v.upper() if v else v


class Summary(BaseModel):
    total_pipe_length_m: float = 0
    fittings: int = 0
    flanges: int = 0
    valves: int = 0
    gaskets: int = 0
    bolt_sets: int = 0
    field_welds: int = 0


class MTOResponse(BaseModel):
    drawing_meta: DrawingMeta
    items: list[MTOItem]
    summary: Summary
    mock: bool = False
    job_id: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
