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

## Converting from RTTTL

The script **`rtttl_to_music.py`** converts [RTTTL](https://en.wikipedia.org/wiki/Ring_Tone_Text_Transfer_Language) (ringtone format) into a single line of toy-piano tokens. Use it to turn an RTTTL tune into numbers you can paste into a `.music` file.

**Usage:**

```bash
python3 rtttl_to_music.py < tune.rtttl
```

- **Input:** RTTTL on stdin (e.g. `Name:d=4,o=5,b=120:c5,e5,g5,c6,...`).
- **Output:** Space-separated tokens on stdout: `0` for rests, `1`–`14` and `1*`–`9*` for keys. No title, comments, or lyrics—only the note sequence.

**Pitch mapping:** The script uses the same piano range as the rest of this project: **G3–F5** (key 1 = G3, key 4 = C4, key 14 = F5). RTTTL octaves 4–7 are supported.

**Transposition:** The **entire melody** is transposed by whole octaves so that it fits on the piano. The script finds the lowest and highest note, then shifts the tune up or down by octaves until the whole range lies between G3 and F5. If the melody spans **more than 22 semitones**, it cannot fit on the 23-key piano; the script prints an error to stderr and exits with code 1.

**Example (paste output into a .music file as one line):**

```bash
echo 'Simpsons:d=4,o=5,b=160:32p,c6,e6,f#6,8a6,g6' | python3 rtttl_to_music.py
# → 0 4 6 5* 9 8  (then add title and use as one music line)
```

---

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

On the physical piano, **key 4** is the white key immediately to the left of two black keys, so **4 = C** (middle C = C4). The full chromatic mapping (low to high) is:

- 1 = G3
- 1* = G♯3
- 2 = A3
- 2* = A♯3
- 3 = B3
- 4 = C4
- 3* = C♯4
- 5 = D4
- 4* = D♯4
- 6 = E4
- 7 = F4
- 5* = F♯4
- 8 = G4
- 6* = G♯4
- 9 = A4
- 7* = A♯4 (between 9 and 10)
- 10 = B4
- 11 = C5
- 8* = C♯5
- 12 = D5
- 9* = D♯5
- 13 = E5
- 14 = F5

Transpose as needed if your instrument is tuned to a different reference.

### Regex for tokens

When parsing or generating, note tokens match:

- **Rest:** `0`
- **White key:** `[1-9]` or `1[0-4]` (i.e. 1–14)
- **Black key:** same numbers with a trailing `*`, e.g. `7*`, `12*`

So the full token pattern is: `0` or `(?:1[0-4]|[1-9])\*?`.

### Examples

**Minimal file (one line, no comments; C major scale 4–11 = C–C):**

```
My Song
4Do 5Re 6Mi 7Fa 8Sol 9La 10Ti 11Do
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
