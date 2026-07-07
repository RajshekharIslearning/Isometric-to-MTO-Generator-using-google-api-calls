import pytest
from pydantic import ValidationError

from app.models import DrawingMeta, MTOItem, MTOResponse, Summary


def test_valid_mto_response():
    resp = MTOResponse(
        drawing_meta=DrawingMeta(drawing_no="ISO-1", nps='6"'),
        items=[
            MTOItem(item_no=1, category="PIPE", description="Pipe", quantity=1, unit="M", length_m=10.0),
        ],
        summary=Summary(total_pipe_length_m=10.0),
    )
    assert resp.items[0].category == "PIPE"
    assert resp.mock is False


def test_rejects_missing_required_field():
    with pytest.raises(ValidationError):
        MTOItem(category="PIPE", description="Pipe", quantity=1, unit="M")  # missing item_no


def test_rejects_bad_category():
    with pytest.raises(ValidationError):
        MTOItem(item_no=1, category="NOT_A_CATEGORY", description="x", quantity=1, unit="EA")


def test_confidence_bounds():
    with pytest.raises(ValidationError):
        MTOItem(item_no=1, category="PIPE", description="x", quantity=1, unit="EA", confidence=1.5)
