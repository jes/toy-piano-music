#!/usr/bin/env python3
"""
Read RTTTL from stdin, output toy-piano number tokens on stdout.
Ignores title, defaults, line breaks, duration/lyrics — only note names and octaves.
P → 0, other notes → 1–14 or 1*–9* (black keys).

The whole melody is transposed by octaves so it fits on the piano (G3–F5, 23 semitones).
If the melody spans more than 22 semitones, exits with an error.
"""

import math
import re
import sys

# Pitch order from render.py: (white_key_number, is_black) from lowest to highest.
# Index 0 = G3 (key 1), index 5 = C4 (key 4), index 22 = F5 (key 14). See README.
PITCH_ORDER = [
    (1, False), (1, True), (2, False), (2, True), (3, False), (4, False), (3, True), (5, False), (4, True),
    (6, False), (7, False), (5, True), (8, False), (6, True), (9, False), (7, True), (10, False), (11, False),
    (8, True), (12, False), (9, True), (13, False), (14, False),
]

# Semitones from C0: G3=43, C4=48, F5=65. Piano has 23 semitones; max span that fits = 22.
G3_SEMITONE = 43
F5_SEMITONE = 65
PIANO_SEMITONES = 23
MAX_SPAN = PIANO_SEMITONES - 1  # 22

# Note name (no octave) -> semitone 0-11 (C=0, C#=1, ..., B=11)
NOTE_SEMITONE = {
    "c": 0, "c#": 1, "db": 1, "d": 2, "d#": 3, "eb": 3, "e": 4, "f": 5, "f#": 6, "gb": 6,
    "g": 7, "g#": 8, "ab": 8, "a": 9, "a#": 10, "bb": 10, "b": 11, "h": 11,
}


def _parse_note_chunk(chunk: str, default_octave: int) -> tuple[bool, int | None]:
    """Return (is_rest, semitone_c0 or None)."""
    # Duration may include a trailing dot (dotted note, e.g. 8. = dotted eighth)
    m = re.match(r"^(\d+\.?)?([Pp]|[A-Ga-gH][#b]?)([4-7])?\.?$", chunk)
    if not m:
        return (True, None)  # skip unparseable as rest
    _dur, note_part, oct_part = m.groups()
    note_part = (note_part or "").strip().lower()
    octave = int(oct_part) if oct_part else default_octave

    if note_part == "p":
        return (True, None)

    if note_part == "h":
        note_part = "b"
    letter = note_part[0]
    acc = ""
    if len(note_part) > 1 and note_part[1] in "#b":
        acc = note_part[1]
    note_name = letter + acc
    if note_name not in NOTE_SEMITONE:
        return (True, None)
    semitone = NOTE_SEMITONE[note_name]
    semitone_c0 = 48 + (octave - 4) * 12 + semitone
    return (False, semitone_c0)


def rtttl_to_tokens(text: str) -> list[str]:
    """Parse RTTTL and return token list. Raises ValueError if melody span > 22 semitones."""
    raw = " ".join(text.split()).strip()
    if not raw:
        return []

    parts = raw.split(":")
    if len(parts) < 2:
        return []
    tone_section = parts[-1].strip()

    default_octave = 5
    if len(parts) >= 2 and "=" in parts[1]:
        for pair in parts[1].split(","):
            pair = pair.strip()
            if pair.lower().startswith("o="):
                try:
                    default_octave = int(pair[2:].strip())
                except ValueError:
                    pass
                break

    # First pass: list of (is_rest, semitone_c0 or None, chunk_text)
    events: list[tuple[bool, int | None, str]] = []
    for chunk in tone_section.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        is_rest, semi = _parse_note_chunk(chunk, default_octave)
        events.append((is_rest, semi, chunk))

    # Filter to notes only for range
    notes_with_chunks = [(s, c) for (rest, s, c) in events if not rest and s is not None]
    if not notes_with_chunks:
        return ["0"] * len(events)

    min_semi, min_chunk = min(notes_with_chunks, key=lambda x: x[0])
    max_semi, max_chunk = max(notes_with_chunks, key=lambda x: x[0])
    span = max_semi - min_semi
    if span > MAX_SPAN:
        raise ValueError(
            f"Melody span is {span} semitones; piano has only {PIANO_SEMITONES} (max span {MAX_SPAN}). "
            f"Lowest note: {min_chunk!r} ({min_semi}); highest note: {max_chunk!r} ({max_semi})"
        )

    # Transpose by whole octaves so [min_semi, max_semi] fits in [G3, F5]
    # offset must satisfy: min_semi + offset >= 43, max_semi + offset <= 65
    # So offset in [43 - min_semi, 65 - max_semi]. Use a multiple of 12.
    offset_lo = G3_SEMITONE - min_semi
    offset_hi = F5_SEMITONE - max_semi
    k_lo = math.ceil(offset_lo / 12)
    k_hi = math.floor(offset_hi / 12)
    if k_lo > k_hi:
        raise ValueError(
            f"Melody cannot fit on piano: need offset in [{offset_lo}, {offset_hi}], "
            f"no multiple of 12 in range"
        )
    k = k_lo
    offset = 12 * k

    # Second pass: convert each event to token
    tokens: list[str] = []
    for is_rest, semitone_c0, _ in events:
        if is_rest or semitone_c0 is None:
            tokens.append("0")
            continue
        s = semitone_c0 + offset
        pitch_index = s - G3_SEMITONE
        assert 0 <= pitch_index < len(PITCH_ORDER), (s, pitch_index)
        num, is_black = PITCH_ORDER[pitch_index]
        tokens.append(f"{num}*" if is_black else str(num))
    return tokens


def main() -> int:
    inp = sys.stdin.read()
    try:
        tokens = rtttl_to_tokens(inp)
    except ValueError as e:
        print(f"rtttl_to_music: {e}", file=sys.stderr)
        return 1
    print(" ".join(tokens))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
