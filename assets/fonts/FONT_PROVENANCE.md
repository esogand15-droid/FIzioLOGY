# Provenance of embedded fonts

- Font family: **Vazirmatn** (SIL Open Font License 1.1) by Saber Rastikerdar.
- Source: https://github.com/rastikerdar/vazirmatn (branch `master`, downloaded via codeload.github.com on 2026-10-24).
- Files embedded: Vazirmatn-Regular.ttf, Vazirmatn-Medium.ttf, Vazirmatn-Bold.ttf, Vazirmatn-Light.ttf
- License file of the upstream project: OFL-1.1 (see upstream repository `OFL.txt`).

## Fallback family (Greek letters, arrows)

- Font family: **DejaVu Sans** (DejaVu Fonts license, a permissive Bitstream Vera derivative).
- Source: system package on the build machine, `/usr/share/fonts/truetype/dejavu/`
  (copied into this repo on 2026-10-25 so the build stays reproducible).
- Why: Vazirmatn has **no Greek glyphs** (`α`, `β`, `μ`) and no arrows (`→`, `←`), which
  the notes use in pharmacology text (`α1`, `β1`) and in flow lines
  (`دریافت ← پردازش ← پاسخ`). Without a fallback those characters are dropped silently.
- Files embedded: DejaVuSans.ttf (regular), DejaVuSans-Bold.ttf (bold).
- The layout engine picks the fallback **per character**, so Persian text keeps
  Vazirmatn and only the missing characters switch family.
