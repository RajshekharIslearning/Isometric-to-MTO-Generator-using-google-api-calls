"""
Takes the raw dict returned by the vision model (or the mock pipeline),
validates it into Pydantic models, derives any missing gasket/bolt rows,
and computes summary totals server-side (never trusting the model's own
arithmetic).
"""

from __future__ import annotations

from pydantic import ValidationError

from app.models import Category, DrawingMeta, MTOItem, MTOResponse, Summary


class PostprocessError(Exception):
    def __init__(self, message: str, detail: str | None = None):
        super().__init__(message)
        self.message = message
        self.detail = detail


def _derive_gasket_bolt_rows(items: list[MTOItem]) -> list[MTOItem]:
    """
    If the model listed flanges/valves but no gaskets/bolts, add derived
    rows: 1 gasket + 1 bolt set per flanged joint. A flanged joint is
    approximated as one per FLANGE item plus one per valve with
    end_type == FLGD (the valve-to-pipe connection also needs a joint).
    Skipped if the model already reported gasket/bolt rows itself.
    """
    has_gaskets = any(i.category == Category.GASKET for i in items)
    has_bolts = any(i.category == Category.BOLT for i in items)
    if has_gaskets and has_bolts:
        return items

    flanged_joints = sum(int(i.quantity) for i in items if i.category == Category.FLANGE)
    flanged_joints += sum(
        int(i.quantity) for i in items if i.category == Category.VALVE and (i.end_type or "").upper() == "FLGD"
    )
    if flanged_joints <= 0:
        return items

    next_no = max((i.item_no for i in items), default=0) + 1
    derived: list[MTOItem] = []

    if not has_gaskets:
        derived.append(
            MTOItem(
                item_no=next_no,
                category="GASKET",
                description="Gasket, Spiral Wound (derived - verify spec against project standard)",
                size_nps=None,
                schedule_rating=None,
                material_spec=None,
                end_type="FLGD",
                quantity=flanged_joints,
                unit="EA",
                confidence=0.5,
                remarks="Derived - 1 per flanged joint, not read directly off drawing",
            )
        )
        next_no += 1

    if not has_bolts:
        derived.append(
            MTOItem(
                item_no=next_no,
                category="BOLT",
                description="Stud Bolt Set (derived - verify spec against project standard)",
                size_nps=None,
                schedule_rating=None,
                material_spec=None,
                end_type="FLGD",
                quantity=flanged_joints,
                unit="SET",
                confidence=0.5,
                remarks="Derived - 1 set per flanged joint, not read directly off drawing",
            )
        )

    return items + derived


def _compute_summary(items: list[MTOItem]) -> Summary:
    return Summary(
        total_pipe_length_m=round(
            sum((i.length_m or 0) for i in items if i.category == Category.PIPE), 3
        ),
        fittings=sum(int(i.quantity) for i in items if i.category == Category.FITTING),
        flanges=sum(int(i.quantity) for i in items if i.category == Category.FLANGE),
        valves=sum(int(i.quantity) for i in items if i.category == Category.VALVE),
        gaskets=sum(int(i.quantity) for i in items if i.category == Category.GASKET),
        bolt_sets=sum(int(i.quantity) for i in items if i.category == Category.BOLT),
        field_welds=sum(
            int(i.quantity)
            for i in items
            if i.category == Category.SUPPORT
            and (
                "field weld" in (i.remarks or "").lower()
                or (i.remarks or "").lower().startswith("fw")
            )
        ),
    )


def process_raw_extraction(raw: dict, mock: bool = False) -> MTOResponse:
    """Validate raw model output and produce the final MTOResponse."""
    try:
        drawing_meta = DrawingMeta(**raw.get("drawing_meta", {}))
        raw_items = raw.get("items", [])
        items = [MTOItem(**item) for item in raw_items]
    except ValidationError as e:
        raise PostprocessError(
            "The extracted data did not match the expected MTO format.",
            detail=str(e),
        ) from e

    if not items:
        raise PostprocessError(
            "No line items were extracted from this drawing.",
            detail="The vision model returned an empty items list.",
        )

    items = _derive_gasket_bolt_rows(items)
    summary = _compute_summary(items)

    return MTOResponse(drawing_meta=drawing_meta, items=items, summary=summary, mock=mock)
