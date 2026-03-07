# Toy piano sheet music

Turn a simple text score into SVG sheet music for a 14-white-key, 9-black-key toy piano.

---

## How to run the tool

```bash
python3 render.py input.music output.svg
```

- **Input:** a `.music` (or any text) file in the format described below.
- **Output:** an SVG file you can open in a browser or import into other tools.

Example:

```bash
python3 render.py incy-wincy-spider.music incy-wincy-spider.svg
```

---

## Input format (for music generation)

Use this section when generating or correcting `.music` files so they work with this renderer. The instrument has **14 white keys** (numbers **1–14**) and **9 black keys** (numbers **1\*–9\***). The physical piano has no 10th black key, so there is **no 10\*** in this format.

### File structure

1. **Line 1:** Song title (required). Any text; it is shown at the top of the sheet.
2. **Optional comment lines:** Lines starting with `#` are shown as centered subtitle text. Use for things like “For 14-key toy piano” or performance notes.
3. **Music lines:** Each non-empty, non-comment line is one line of music. A line is a sequence of **tokens** with **lyrics** in between.

### Tokens

- **White key:** a number from 1 to 14, e.g. `7` or `14`.
- **Black key:** a number from 1 to 9 with an asterisk, e.g. `7*` or `3*`. The piano has only 9 black keys, so there is no `10*`.
- **Rest / gap:** the digit `0`. Use for a brief pause or to align lyrics (no note is played).

Tokens are written **directly against** the following lyric text; there is no space between the token and the start of the lyric. Example: `7In-7cy` means note 7 with lyric “In-”, then note 7 with lyric “cy”.

### Pitch order (critical for correct placement)

Notes are placed on the staff by **pitch order**, not by the white-key number alone. The ascending order of all 24 keys is:

```
1  1*  2  2*  3  4  3*  5  4*  6  7  5*  8  6*  9  7*  10  11  8*  12  9*  13  14
```

So for example:

- **7\*** is **between 9 and 10** in pitch (not next to 7). Use `7*` when you want the black key between white keys 9 and 10.
- **5\*** is between 7 and 8.
- **6\*** is between 8 and 9.
- **8\*** is between 11 and 12.
- **9\*** is between 13 and 14.

When generating or correcting music, use this order to choose the right token for each pitch.

### Mapping to note names (e.g. C4, D4)

If you assume the **first white key (1)** is **C4**, then each token maps to a note as follows (low to high, same order as the pitch list above):

- 1 = C4
- 1* = C♯4
- 2 = D4
- 2* = D♯4
- 3 = E4
- 4 = F4
- 3* = F♯4
- 5 = G4
- 4* = G♯4
- 6 = A4
- 7 = B4
- 5* = A♯4 (between 6 and 7)
- 8 = C5
- 6* = C♯5
- 9 = D5
- 7* = D♯5 (between 9 and 10)
- 10 = E5
- 11 = F5
- 8* = F♯5
- 12 = G5
- 9* = G♯5
- 13 = A5
- 14 = B5

Transpose as needed if the instrument starts on a different note.

### Regex for tokens

When parsing or generating, note tokens match:

- **Rest:** `0`
- **White key:** `[1-9]` or `1[0-4]` (i.e. 1–14)
- **Black key:** same numbers with a trailing `*`, e.g. `7*`, `12*`

So the full token pattern is: `0` or `(?:1[0-4]|[1-9])\*?`.

### Examples

**Minimal file (one line, no comments):**

```
My Song
1Do 2Re 3Mi 4Fa 5Sol 6La 7Ti 8Do
```

**With comments and rests:**

```
Incy Wincy Spider
# For 14-key toy piano
# 0 means a rough gap, n* means black key

7In-7cy 7win-8cy 9spi-9der 7climbed 8up 7the 8wa-9ter 7spout.
9Down 9came 7*the 11rain 11and 7*washed 9the 7*spi-11der 9out.
```

**Using black keys (7\* between 9 and 10):**

```
9 7* 10
```
sounds ascending: D5, D♯5, E5 (if 1=C4).

**Rest (0) for a beat with no note:**

```
5Hey 0 5ho 0 5hey 0 5ho
```

### Checklist for one-shot correct input

- First line is the title.
- Optional lines starting with `#` are comments.
- Every other non-empty line is a music line: a sequence of tokens with lyrics in between (no space between a token and the following lyric).
- Use **1–14** for white keys, **1\*–9\*** for black keys (no 10\*).
- Use **0** for a rest/gap.
- For correct staff placement, use the **pitch order** above: e.g. use **7\*** for the note between 9 and 10, not for the note next to 7.
