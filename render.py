#!/usr/bin/env python3

from __future__ import annotations

import html
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path


TOKEN_RE = re.compile(r"(0|(?:1[0-4]|[1-9])\*?)")


WHITE_KEY_COLOURS = {
    1: "#6f42c1",   # purple
    2: "#8e5cc7",   # violet
    3: "#e8a3b5",   # pale pink
    4: "#d81b60",   # pink/red
    5: "#e53935",   # red
    6: "#f57c00",   # orange
    7: "#fbc02d",   # yellow
    8: "#43a047",   # green
    9: "#2e7d32",   # dark green
    10: "#00acc1",  # teal
    11: "#81d4fa",  # light blue
    12: "#42a5f5",  # blue
    13: "#3949ab",  # indigo
    14: "#8d6e63",  # brown
}

# Reference pitch order (same as .music / rtttl_to_music); kept for docs cross-reference.
PITCH_ORDER = [
    (1, False), (1, True), (2, False), (2, True), (3, False), (4, False), (3, True), (5, False), (4, True),
    (6, False), (7, False), (5, True), (8, False), (6, True), (9, False), (7, True), (10, False), (11, False),
    (8, True), (12, False), (9, True), (13, False), (14, False),
]

# Treble staff: y-position uses half-steps of the staff (integer = line, .5 = space).
# Bottom line = white key 6 (E4); top line = white key 14 (F5). Ledger lines extend for keys 1–5.
# Black keys sit midway between the staff positions of the two white keys they lie between chromatically.
_WHITE_KEY_STAFF_POS: dict[int, float] = {
    1: 6.5,
    2: 6.0,
    3: 5.5,
    4: 5.0,
    5: 4.5,
    6: 4.0,
    7: 3.5,
    8: 3.0,
    9: 2.5,
    10: 2.0,
    11: 1.5,
    12: 1.0,
    13: 0.5,
    14: 0.0,
}
# n* lies between these white keys (see README pitch order).
_BLACK_BETWEEN_WHITE: dict[int, tuple[int, int]] = {
    1: (1, 2),
    2: (2, 3),
    3: (4, 5),
    4: (5, 6),
    5: (7, 8),
    6: (8, 9),
    7: (9, 10),
    8: (11, 12),
    9: (12, 13),
}

LEFT_MARGIN = 90
RIGHT_MARGIN = 24  # content can sit close to the right edge
# Staff horizontal extent: extend left to the treble clef (clef is at LEFT_MARGIN - 28)
STAFF_LEFT = LEFT_MARGIN - 40
TOP_MARGIN = 40
TITLE_GAP = 20
COMMENT_LINE_HEIGHT = 20
STAFF_TOP = 20
STAFF_GAP = 11  # vertical spacing between staff lines (larger = bigger staff and notes)
LINE_HEIGHT = 100  # vertical space per system (smaller = less gap between lines of music)
NOTE_SPACING = 44
# Note circle: large enough to fully contain the number; radius independent of digit size
NOTE_RADIUS = STAFF_GAP * 0.78
# Fixed digit size so circles can be bigger without numbers overflowing
NOTE_DIGIT_SIZE = 13
# Lyrics sit just below the staff (or below lowest note/ledger if lower)
LYRIC_CLEARANCE = 18  # gap between lowest note/ledger and lyric baseline
LYRIC_LINE_HEIGHT = 14
GAP_AFTER_LYRIC = 12

# Treble clef: path designed for viewBox "0 0 12 40", height 40 units;
# we scale so 8 units = one staff space (STAFF_GAP). Center of spiral on 2nd line.
TREBLE_CLEF_PATH = (
    "M2 2v36 M2 20c0-4 2-8 6-8s6 4 6 8-2 8-6 8-6-4-6-8z "
    "M2 20c0 4 2 8 6 8 M2 12c2-2 4-2 6 0 M2 28c2 2 4 2 6 0"
)
TREBLE_CLEF_WIDTH = 14  # units in same scale as path height 40
TREBLE_CLEF_HEIGHT = 40


def staff_y(y0: float, position: float) -> float:
    """Y coordinate for a staff position. position 0 = top line, 4 = bottom line (half-steps)."""
    return y0 + STAFF_TOP + position * STAFF_GAP


def _staff_position(number: int, is_black: bool) -> float:
    """Staff position: 0=top line (F5), 4=bottom line (E4); half-integers are spaces; >4 / <0 use ledgers."""
    if is_black:
        lo, hi = _BLACK_BETWEEN_WHITE[number]
        a = _WHITE_KEY_STAFF_POS[lo]
        b = _WHITE_KEY_STAFF_POS[hi]
        return (a + b) / 2.0
    return _WHITE_KEY_STAFF_POS[number]


def note_cy(y0: float, number: int, is_black: bool) -> float:
    """Y coordinate for note center: diatonic staff steps for white keys; midway between those for black keys."""
    position = _staff_position(number, is_black)
    return staff_y(y0, position)


def note_position(number: int, is_black: bool) -> float:
    """Staff position (0=top line, 4=bottom line). For ledger line logic: >4 = below staff, <0 = above."""
    return _staff_position(number, is_black)


@dataclass
class Event:
    kind: str  # "white", "black", "rest"
    number: int | None
    lyric: str


@dataclass
class Song:
    title: str
    comments: list[str]
    lines: list[list[Event]]


def parse_music_line(line: str) -> list[Event]:
    matches = list(TOKEN_RE.finditer(line))
    if not matches:
        raise ValueError(f"No note tokens found in music line: {line!r}")

    events: list[Event] = []

    for i, match in enumerate(matches):
        token = match.group(1)
        lyric_start = match.end()
        lyric_end = matches[i + 1].start() if i + 1 < len(matches) else len(line)
        lyric = line[lyric_start:lyric_end]

        if token == "0":
            events.append(Event(kind="rest", number=None, lyric=lyric))
            continue

        if token.endswith("*"):
            number = int(token[:-1])
            events.append(Event(kind="black", number=number, lyric=lyric))
        else:
            number = int(token)
            events.append(Event(kind="white", number=number, lyric=lyric))

    return events


def parse_song(text: str) -> Song:
    raw_lines = text.splitlines()
    if not raw_lines:
        raise ValueError("Input file is empty")

    title = raw_lines[0].strip()
    if not title:
        raise ValueError("First line must contain the song title")

    comments: list[str] = []
    music_lines: list[list[Event]] = []

    for raw in raw_lines[1:]:
        if not raw.strip():
            continue
        if raw.startswith("#"):
            comments.append(raw[1:].lstrip())
            continue
        music_lines.append(parse_music_line(raw.rstrip()))

    if not music_lines:
        raise ValueError("No music lines found")

    return Song(title=title, comments=comments, lines=music_lines)


def svg_text(
    x: float,
    y: float,
    text: str,
    *,
    size: int = 16,
    anchor: str = "start",
    weight: str = "normal",
    fill: str = "#222",
    family: str = "sans-serif",
) -> str:
    return (
        f'<text x="{x}" y="{y}" '
        f'font-family="{family}" font-size="{size}" font-weight="{weight}" '
        f'text-anchor="{anchor}" fill="{fill}">{html.escape(text)}</text>'
    )


def estimate_width(lines: list[list[Event]]) -> int:
    """Width is driven by the longest line so all staves share the same width."""
    max_events = max(len(line) for line in lines)
    return LEFT_MARGIN + max_events * NOTE_SPACING + RIGHT_MARGIN


def _content_bottom(y0: float, line: list[Event]) -> float:
    """Lowest y (bottom of notes/ledgers) for this system so lyrics can sit below."""
    bottom = y0 + STAFF_TOP + 4 * STAFF_GAP
    for event in line:
        if event.kind == "rest":
            continue
        assert event.number is not None
        cy = note_cy(y0, event.number, event.kind == "black")
        pos = note_position(event.number, event.kind == "black")
        bottom = max(bottom, cy + NOTE_RADIUS)
        if pos > 4:
            for k in range(5, math.ceil(pos) + 1):
                bottom = max(bottom, staff_y(y0, float(k)) + 2)
    return bottom


def _compute_line_layout(song: Song, music_top: float) -> tuple[list[float], list[float]]:
    """Compute y0 and lyric baseline for each system (variable height when lines have low notes)."""
    line_y0s: list[float] = []
    line_lyric_baselines: list[float] = []
    y0 = music_top
    for line in song.lines:
        line_y0s.append(y0)
        content_bottom = _content_bottom(y0, line)
        lyric_baseline = content_bottom + LYRIC_CLEARANCE
        line_lyric_baselines.append(lyric_baseline)
        # Minimum system height so lines without low notes still have comfortable spacing
        system_height = max(
            LINE_HEIGHT,
            lyric_baseline - y0 + LYRIC_LINE_HEIGHT + GAP_AFTER_LYRIC,
        )
        y0 += system_height
    return line_y0s, line_lyric_baselines


def render_song(song: Song) -> str:
    width = estimate_width(song.lines)
    comments_height = len(song.comments) * COMMENT_LINE_HEIGHT
    music_top = TOP_MARGIN + 36 + TITLE_GAP + comments_height + 10
    line_y0s, line_lyric_baselines = _compute_line_layout(song, music_top)
    total_music_height = line_lyric_baselines[-1] + LYRIC_LINE_HEIGHT + GAP_AFTER_LYRIC - music_top
    height = music_top + total_music_height + 30

    out: list[str] = []
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">')
    out.append('<rect width="100%" height="100%" fill="white"/>')

    # Title
    out.append(svg_text(width / 2, TOP_MARGIN, song.title, size=28, anchor="middle", family="serif"))

    # Comments
    comment_y = TOP_MARGIN + 36
    for comment in song.comments:
        out.append(svg_text(width / 2, comment_y, comment, size=14, anchor="middle", fill="#555"))
        comment_y += COMMENT_LINE_HEIGHT

    # Music lines
    for line_index, line in enumerate(song.lines):
        y0 = line_y0s[line_index]
        lyric_baseline = line_lyric_baselines[line_index]
        staff_right = width - RIGHT_MARGIN
        staff_top_y = y0 + STAFF_TOP
        staff_bottom_y = y0 + STAFF_TOP + 4 * STAFF_GAP

        # Staff: 5 horizontal lines extending to left edge of treble clef and to right margin
        for i in range(5):
            y = staff_top_y + i * STAFF_GAP
            out.append(
                f'<line x1="{STAFF_LEFT}" y1="{y}" x2="{staff_right}" y2="{y}" '
                f'stroke="#444" stroke-width="1"/>'
            )
        # Vertical lines at left and right edges of the staff
        out.append(
            f'<line x1="{STAFF_LEFT}" y1="{staff_top_y}" x2="{STAFF_LEFT}" y2="{staff_bottom_y}" '
            f'stroke="#444" stroke-width="1"/>'
        )
        out.append(
            f'<line x1="{staff_right}" y1="{staff_top_y}" x2="{staff_right}" y2="{staff_bottom_y}" '
            f'stroke="#444" stroke-width="1"/>'
        )

        # Treble clef (Unicode U+1D11E) scaled to span ~4 staff spaces, aligned so G is on 2nd line
        clef_x = LEFT_MARGIN - 28
        clef_font_size = int(STAFF_GAP * 5)
        clef_y = y0 + STAFF_TOP + 2 * STAFF_GAP + clef_font_size * 0.35  # baseline so G line is 2nd
        out.append(
            f'<text x="{clef_x}" y="{clef_y}" font-size="{clef_font_size}" '
            f'font-family="FreeSerif, DejaVu Serif, Times New Roman, serif" '
            f'text-anchor="middle" fill="#222">&#x1D11E;</text>'
        )

        x = LEFT_MARGIN

        for event in line:
            cx = x
            if event.kind == "rest":
                rest_y = y0 + STAFF_TOP + 2 * STAFF_GAP
                out.append(svg_text(cx, rest_y, "·", size=int(14 + STAFF_GAP * 1.5), anchor="middle", fill="#888"))
                if event.lyric:
                    out.append(svg_text(cx, lyric_baseline, event.lyric, size=14, anchor="middle"))
                x += NOTE_SPACING
                continue

            assert event.number is not None
            cy = note_cy(y0, event.number, event.kind == "black")
            pos = note_position(event.number, event.kind == "black")

            # Ledger lines for notes below the staff (position > 4)
            if pos > 4:
                for k in range(5, math.ceil(pos) + 1):
                    led_y = staff_y(y0, float(k))
                    led_x1 = cx - NOTE_RADIUS * 2.2
                    led_x2 = cx + NOTE_RADIUS * 2.2
                    out.append(
                        f'<line x1="{led_x1}" y1="{led_y}" x2="{led_x2}" y2="{led_y}" '
                        f'stroke="#444" stroke-width="1"/>'
                    )
            # Ledger lines for notes above the staff (position < 0)
            if pos < 0:
                for k in range(math.ceil(pos), 0):
                    led_y = staff_y(y0, float(k))
                    led_x1 = cx - NOTE_RADIUS * 2.2
                    led_x2 = cx + NOTE_RADIUS * 2.2
                    out.append(
                        f'<line x1="{led_x1}" y1="{led_y}" x2="{led_x2}" y2="{led_y}" '
                        f'stroke="#444" stroke-width="1"/>'
                    )

            if event.kind == "black":
                fill = "#222"
                text_fill = "#fff"
            else:
                fill = WHITE_KEY_COLOURS[event.number]
                text_fill = "#fff"

            out.append(f'<circle cx="{cx}" cy="{cy}" r="{NOTE_RADIUS}" fill="{fill}" stroke="none"/>')
            out.append(svg_text(cx, cy + 4, str(event.number), size=NOTE_DIGIT_SIZE, anchor="middle", weight="bold", fill=text_fill))

            if event.lyric:
                out.append(svg_text(cx, lyric_baseline, event.lyric, size=14, anchor="middle"))

            x += NOTE_SPACING

    out.append("</svg>")
    return "\n".join(out)


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python3 render.py input.music output.svg", file=sys.stderr)
        return 1

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    try:
        song = parse_song(input_path.read_text(encoding="utf-8"))
        svg = render_song(song)
        output_path.write_text(svg, encoding="utf-8")
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
