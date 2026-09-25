# PineTime Canvas faces

Watch faces for the **Canvas** watch face in [InfiniTime](https://github.com/InfiniTimeOrg/InfiniTime).
Canvas draws whatever a small text file describes, so a new face is just a `.cfg` file
(plus any images or fonts it uses) copied to the watch — no firmware rebuild.

On the watch, double-tap the right third of the screen for the next face and the left
third for the previous one.

## Layout

```
faces/<name>/<name>.cfg     the face           ->  /canvas/<name>.cfg on the watch
faces/<name>/*              its assets         ->  /canvas/<name>/ on the watch
tools/check.py              structural checks run by CI
tools/install-sim.sh        copy faces into an InfiniSim flash image
tools/make-frames.py        pre-render rotated frames for image hands
```

Face folder names must be short: `<name>.cfg` has to fit in 31 characters.

Faces may also use the fonts and images from the standard InfiniTime resources package
(`/fonts/teko.bin`, `/images/pine_small.bin`, …); `tools/check.py` has the full list.

## Trying faces in the simulator

With the simulator closed, from the directory holding `spiNorFlash.raw`:

```sh
path/to/pinetime-canvas-faces/tools/install-sim.sh ./build_sim/littlefs-do          # all faces
path/to/pinetime-canvas-faces/tools/install-sim.sh ./build_sim/littlefs-do digital  # just one
```

## Format

One element per line, drawn in file order (later lines on top). Lines are at most 127 bytes.
Lines starting with `#` are comments.

```
# This is an example showing a beach background image that changes at night.
requires 1
name Beach
bg #003366
image 0 0 /canvas/beach/bg.bin
image 0 0 /canvas/beach/night.bin if hour>=20
text 120 60 font=jetbrains_mono_76 align=center "{HH}:{mm}"
text 120 150 color=#AAAAAA align=center "{ddd} {D} {MMM}"
text 120 180 color=#FFCC00 align=center "Taco Tuesday!" if dow=2 hour>=11 hour<14
```

### Directives

| line | meaning |
|---|---|
| `requires N` | format version the face needs; must be the first non-comment line. Older firmware shows an error instead of misdrawing. |
| `name Some Name` | shown briefly when switching to the face (default: file name) |
| `bg #RRGGBB` | background color (default black) |

### Elements

| element | arguments | notes |
|---|---|---|
| `text` | `x y "template"` | `align=left\|center\|right` anchors at x; y is the top |
| `image` | `x y /path/img.bin` | LVGL binary image |
| `rect` | `x y w h` | `radius`, `border`, `border_color` |
| `line` | `x1 y1 x2 y2` | square ends unless `rounded=on` |
| `arc` | `x y w h` | `start`/`end` in degrees, 0 = 12 o'clock, clockwise |
| `hand hour\|minute\|second\|steps` | `x y w h` (pivots on the box centre) | `radius` = length, `inner` = start distance (negative for a tail); `steps` sweeps once per step goal; `image=` draws a picture instead of a line (see below) |
| `ticks` | `x y w h` | `count`, `outer`, `inner`, optional `start`/`end` |
| `battery` | `x y` | battery icon with fill level |
| `bar` | `x y w h` | `value=<field> min= max= dir=up\|down\|left\|right` |

Common attributes: `color=#RRGGBB` (or `battery` / `batteryLow` to follow the charge), `width`,
`opa=0..255`, `font`, `case=upper|lower`, `recolor=on` (LVGL `#rrggbb text#` markup), `rounded=on|off`.

`left=N` / `right=N` place an element N pixels left/right of the previous one, vertically centred on
it; empty or hidden neighbours are skipped, so rows of status icons collapse naturally.

Fonts: `jetbrains_mono_bold_20` (default, includes the UI icons), `jetbrains_mono_42`,
`jetbrains_mono_76`, `jetbrains_mono_extrabold_compressed`, `open_sans_light`, `lv_font_sys_48`,
`fontawesome_weathericons`, or a font file such as `/canvas/<name>/myfont.bin` (at most 4 per face).
The larger built-in fonts contain digits only.

### Image hands

Canvas can't rotate images, so a hand drawn as a picture uses one pre-rendered frame per angle.
The frame nearest the hand's angle is centred on the point `radius` pixels out from the pivot:

```
hand minute 0 0 240 240 radius=80 width=6 color=#000000
hand minute 0 0 240 240 radius=80 image=/canvas/mickey/glove{frame:02}.bin frames=60
```

`{frame}` is replaced by the frame number, 0 at 12 o'clock counting clockwise (`{frame:02}` pads it to
two digits). `frames` defaults to 60. The pair above draws a line for the arm and a glove at its end;
the same frames can serve both the hour and the minute hand.

Make the frames with `tools/make-frames.py` from one picture drawn pointing up (needs Pillow):

```sh
tools/make-frames.py glove.png faces/mickey --name glove --center 14,26 --preview sheet.png
```

`--center` is the point in the picture that sits at the end of the arm (default: the middle). Frames
are 16-colour by default, which keeps 60 small gloves to about 120 KB; `--format truecolor` gives full
colour at about six times the size.

### Fields

Time: `year month day yday daysLeft week weekUS dow hour hour12 minute second tenth`
(`dow` 1 = Monday … 7 = Sunday; `week` is the ISO week).

Status: `battery charging power ble bleOn notify steps stepPct hr hrOn alarm weather temp clock12`
(on/off values are 0 or 1; `clock12` is the watch's 12-hour setting).

### Conditions

Anything after `if` on a line is a list of conditions, all of which must hold:
`field<op>value` with no spaces, where op is `=`, `<`, `>`, `<=` or `>=`. At most 6 per element.

### Text placeholders

- Any field: `{steps}`, `{yday:3}` (padded with spaces), `{battery:03}` (padded with zeros)
- Shorthands: `{YYYY} {YY} {M} {MM} {MMM} {D} {DD} {ddd} {dddd} {H} {HH} {h} {hh} {mm} {ss} {A} {t}`
- Icons, empty when not applicable: `{ble} {plug} {notify} {alarm} {heart} {shoe} {wIcon} {wText} {tempU}`
- `\n` starts a new line

### Battery life

A face only redraws as often as it needs to: once a minute, unless it shows seconds or has a minute or
second hand (every second) or uses `tenth` (up to ten times a second). Keep large blinking elements off
image backgrounds, since the image is re-read from flash each time they change.

## Contributing

1. Add `faces/<name>/<name>.cfg`, with any assets beside it, referenced as `/canvas/<name>/...`.
2. Try it in the simulator (or on a watch).
3. Run `python tools/check.py` and include a screenshot in the pull request.

By contributing a face you agree to release it, including its assets, under the license below,
and confirm that you have the right to do so (fonts and images included).

## License

The faces in `faces/` are licensed under [Creative Commons Attribution 4.0 International](LICENSE)
(CC BY 4.0): use, share and adapt them freely, including commercially, as long as you credit the
author. Each face's author is recorded in its folder's commit history.

The exception is any face whose `.cfg` starts with an `SPDX-License-Identifier` comment naming a
different license. The recreations of InfiniTime's built-in faces (analog, casio, digital, infineat,
pinetimestyle, the pride flags, terminal) are derived from
[InfiniTime](https://github.com/InfiniTimeOrg/InfiniTime)'s source and so are
[GPL-3.0](LICENSES/GPL-3.0.txt), like InfiniTime itself.

If your face adapts someone else's work, add an SPDX line with the license that work requires, and
say where it came from on the next line.

The scripts in `tools/` are under the [MIT License](tools/LICENSE).
