"""
Deterministic mock MTO used when GEMINI_API_KEY is not configured, or when
the live pipeline fails and MOCK_FALLBACK_ON_ERROR=true. This lets the app
run and be evaluated with zero external setup, per the brief's requirement
to handle "AI service failures" gracefully rather than crashing.
"""

from app.models import DrawingMeta, MTOItem, MTOResponse, Summary


def build_mock_response() -> MTOResponse:
    drawing_meta = DrawingMeta(
        drawing_no="ISO-1501-01",
        revision="2",
        line_number='6"-P-1501-A1A-IH',
        nps='6"',
        material_class="A1A",
        service="Process",
    )

    items = [
        MTOItem(item_no=1, category="PIPE", description="Pipe, Seamless, BE, ASME B36.10",
                size_nps='6"', schedule_rating="SCH 40", material_spec="ASTM A106 Gr.B",
                end_type="BW", quantity=12.45, unit="M", length_m=12.45, confidence=0.94),
        MTOItem(item_no=2, category="FITTING", description="Elbow 90 deg LR, BW",
                size_nps='6"', schedule_rating="SCH 40", material_spec="ASTM A234 WPB",
                end_type="BW", quantity=4, unit="EA", confidence=0.88),
        MTOItem(item_no=3, category="FITTING", description="Tee, Equal, BW",
                size_nps='6"', schedule_rating="SCH 40", material_spec="ASTM A234 WPB",
                end_type="BW", quantity=1, unit="EA", confidence=0.81),
        MTOItem(item_no=4, category="FITTING", description="Reducer, Concentric, BW",
                size_nps='6"x4"', schedule_rating="SCH 40", material_spec="ASTM A234 WPB",
                end_type="BW", quantity=1, unit="EA", confidence=0.76),
        MTOItem(item_no=5, category="FLANGE", description="Flange, Weld-Neck, RF",
                size_nps='6"', schedule_rating="CL150", material_spec="ASTM A105",
                end_type="BW", quantity=2, unit="EA", confidence=0.91),
        MTOItem(item_no=6, category="VALVE", description="Gate Valve, Flanged, RF",
                size_nps='6"', schedule_rating="CL150", material_spec="ASTM A216 WCB",
                end_type="FLGD", quantity=1, unit="EA", confidence=0.85),
        MTOItem(item_no=7, category="GASKET", description="Gasket, Spiral Wound, SS316/Graphite",
                size_nps='6"', schedule_rating="CL150", material_spec="SS316/Graphite",
                end_type="FLGD", quantity=2, unit="EA", confidence=0.6,
                remarks="Derived - 1 per flanged joint"),
        MTOItem(item_no=8, category="BOLT", description="Stud Bolt w/ 2 Nuts",
                size_nps='3/4"', schedule_rating="-", material_spec="A193 B7 / A194 2H",
                end_type="FLGD", quantity=2, unit="SET", confidence=0.6,
                remarks="Derived - 1 set per flanged joint"),
        MTOItem(item_no=9, category="SUPPORT", description="Pipe Shoe, Fixed",
                size_nps='6"', schedule_rating=None, material_spec="CS",
                end_type=None, quantity=1, unit="EA", confidence=0.75,
                remarks="field weld to structure"),
    ]

    # Summary is computed server-side by _compute_summary in production.
    # For the mock, we pre-compute matching values so the totals are consistent.
    summary = Summary(
        total_pipe_length_m=12.45,
        fittings=6,
        flanges=2,
        valves=1,
        gaskets=2,
        bolt_sets=2,
        field_welds=1,
    )

    return MTOResponse(drawing_meta=drawing_meta, items=items, summary=summary, mock=True)
