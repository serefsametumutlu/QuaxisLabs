"""`tlab/viz/svg/prim.py` -- saf string üreteçleri."""

from __future__ import annotations

from tlab.viz.svg.prim import (
    escape_xml,
    pill,
    svg_circle,
    svg_line,
    svg_poly,
    svg_rect,
    svg_text,
)


def test_escape_xml_escapes_all_five_chars() -> None:
    assert escape_xml("""a&b<c>d"e'f""") == "a&amp;b&lt;c&gt;d&quot;e&apos;f"


def test_svg_line_basic_attrs() -> None:
    out = svg_line(1, 2, 3, 4, stroke="#fff", width=2)
    assert '<line x1="1" y1="2" x2="3" y2="4"' in out
    assert 'stroke="#fff"' in out
    assert 'stroke-width="2"' in out


def test_svg_line_omits_none_attrs() -> None:
    out = svg_line(0, 0, 1, 1)
    assert "stroke-dasharray" not in out
    assert "filter" not in out


def test_svg_rect_negative_height_flips() -> None:
    out = svg_rect(10, 50, 20, -10)
    assert 'y="40"' in out
    assert 'height="10"' in out


def test_svg_rect_min_height_clamped() -> None:
    out = svg_rect(0, 0, 10, 0.1)
    assert 'height="0.6"' in out


def test_svg_poly_polygon_and_polyline() -> None:
    pts = [(0, 0), (1, 1), (2, 0)]
    poly = svg_poly("polygon", pts, fill="red")
    line = svg_poly("polyline", pts, stroke="blue")
    assert poly.startswith("<polygon")
    assert line.startswith("<polyline")
    assert 'points="0,0 1,1 2,0"' in poly


def test_svg_text_escapes_content() -> None:
    out = svg_text(0, 0, "A&B")
    assert ">A&amp;B<" in out


def test_svg_circle_basic() -> None:
    out = svg_circle(5, 5, 3, fill="none", stroke="black")
    assert 'cx="5"' in out
    assert 'r="3"' in out


def test_pill_produces_rect_and_centered_text() -> None:
    out = pill(0, 0, 100, 20, "AL", text_fill="#fff")
    assert "<rect" in out
    assert "<text" in out
    assert 'text-anchor="middle"' in out
    assert ">AL<" in out


def test_fnum_drops_trailing_zero_for_integers() -> None:
    out = svg_line(1.0, 2.0, 3.0, 4.0)
    assert 'x1="1"' in out and 'y1="2"' in out
