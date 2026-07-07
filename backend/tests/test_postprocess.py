"""
Tests for the post-processing pipeline: gasket/bolt derivation and
server-side summary computation.
"""

from __future__ import annotations

import pytest

from app.models import Category, MTOItem
from app.pipeline.postprocess import (
    PostprocessError,
    _compute_summary,
    _derive_gasket_bolt_rows,
    process_raw_extraction,
)


def _make_item(
    item_no: int,
    category: str,
    quantity: float = 1,
    end_type: str | None = None,
    length_m: float | None = None,
    remarks: str | None = None,
) -> MTOItem:
    return MTOItem(
        item_no=item_no,
        category=category,
        description=f"Test {category}",
        quantity=quantity,
        unit="EA",
        end_type=end_type,
        length_m=length_m,
        remarks=remarks,
    )


class TestDeriveGasketBoltRows:
    def test_no_flanges_no_derivation(self):
        items = [_make_item(1, "PIPE", length_m=5.0), _make_item(2, "FITTING")]
        result = _derive_gasket_bolt_rows(items)
        assert len(result) == 2

    def test_derives_gasket_and_bolt_for_flanges(self):
        items = [
            _make_item(1, "PIPE", length_m=5.0),
            _make_item(2, "FLANGE", quantity=2),
        ]
        result = _derive_gasket_bolt_rows(items)
        categories = {i.category for i in result}
        assert Category.GASKET in categories
        assert Category.BOLT in categories
        gasket = next(i for i in result if i.category == Category.GASKET)
        assert gasket.quantity == 2

    def test_derives_for_flanged_valves(self):
        items = [
            _make_item(1, "FLANGE", quantity=2),
            _make_item(2, "VALVE", quantity=1, end_type="FLGD"),
        ]
        result = _derive_gasket_bolt_rows(items)
        gasket = next(i for i in result if i.category == Category.GASKET)
        # 2 flanges + 1 FLGD valve = 3 flanged joints
        assert gasket.quantity == 3

    def test_no_derivation_if_already_present(self):
        items = [
            _make_item(1, "FLANGE", quantity=2),
            _make_item(2, "GASKET", quantity=2),
            _make_item(3, "BOLT", quantity=2),
        ]
        result = _derive_gasket_bolt_rows(items)
        assert len(result) == 3  # no new rows added

    def test_partial_derivation_missing_only_gaskets(self):
        items = [
            _make_item(1, "FLANGE", quantity=2),
            _make_item(2, "BOLT", quantity=2),
        ]
        result = _derive_gasket_bolt_rows(items)
        # Only gaskets should be added (bolts already present)
        gaskets = [i for i in result if i.category == Category.GASKET]
        bolts = [i for i in result if i.category == Category.BOLT]
        assert len(gaskets) == 1
        assert len(bolts) == 1  # still only original


class TestComputeSummary:
    def test_pipe_length_sums_correctly(self):
        items = [
            _make_item(1, "PIPE", quantity=5.5, length_m=5.5),
            _make_item(2, "PIPE", quantity=3.0, length_m=3.0),
        ]
        summary = _compute_summary(items)
        assert summary.total_pipe_length_m == 8.5

    def test_counts_by_category(self):
        items = [
            _make_item(1, "FITTING"),
            _make_item(2, "FITTING"),
            _make_item(3, "FLANGE"),
            _make_item(4, "VALVE"),
            _make_item(5, "GASKET"),
            _make_item(6, "BOLT"),
        ]
        summary = _compute_summary(items)
        assert summary.fittings == 2
        assert summary.flanges == 1
        assert summary.valves == 1
        assert summary.gaskets == 1
        assert summary.bolt_sets == 1

    def test_field_welds_counted_via_remarks(self):
        items = [
            _make_item(1, "SUPPORT", remarks="field weld to structure"),
            _make_item(2, "SUPPORT", remarks="shop weld"),
        ]
        summary = _compute_summary(items)
        assert summary.field_welds == 1


class TestProcessRawExtraction:
    def _minimal_raw(self) -> dict:
        return {
            "drawing_meta": {"drawing_no": "ISO-TEST-01"},
            "items": [
                {
                    "item_no": 1,
                    "category": "PIPE",
                    "description": "Pipe",
                    "quantity": 10.0,
                    "unit": "M",
                    "length_m": 10.0,
                    "confidence": 0.9,
                }
            ],
        }

    def test_happy_path(self):
        result = process_raw_extraction(self._minimal_raw())
        assert result.drawing_meta.drawing_no == "ISO-TEST-01"
        assert len(result.items) >= 1
        assert result.summary.total_pipe_length_m == 10.0

    def test_raises_on_empty_items(self):
        raw = {"drawing_meta": {}, "items": []}
        with pytest.raises(PostprocessError, match="No line items"):
            process_raw_extraction(raw)

    def test_raises_on_invalid_item(self):
        raw = {
            "drawing_meta": {},
            "items": [{"item_no": 1, "category": "INVALID_CAT", "description": "x", "quantity": 1, "unit": "EA"}],
        }
        with pytest.raises(PostprocessError):
            process_raw_extraction(raw)

    def test_mock_flag_propagated(self):
        result = process_raw_extraction(self._minimal_raw(), mock=True)
        assert result.mock is True
