# Print guide

Contents: pixel to size, built-in tool limits, white border, die-cut line, sheets, color, checklist

## Pixel to print size

Print size in inches = pixels / dpi. At 300 dpi:

| Pixels (short side) | Size at 300 dpi |
|---|---|
| 1024 | 3.4 in, 87 mm |
| 1254 | 4.2 in, 106 mm |
| 1536 | 5.1 in, 130 mm |
| 2048 | 6.8 in, 173 mm |

The sticker shape usually fills 70 to 90 percent of the canvas, so the printed sticker is smaller than the canvas. Measure the content bounding box and compute from it.

## Built-in Codex tool limits

No size argument. Output is about 1254 to 1536 px. For a 50 mm sticker at 300 dpi you need about 590 px of content, so this is enough. For A4 sheets with large stickers (over 100 mm), content may fall under 300 dpi. State the real dpi to the user. Do not upscale to hide it; if larger is needed, use an API provider with size control.

## White border

Many print shops expect a white outline around the art so edges are clean.

- Add it after generation with an image step (Pillow and numpy; no script for it yet): dilate the alpha, fill with white, keep the original art on top. That is image processing on the shape, not text.
- Width: 2 to 3 mm at print size (about 24 to 35 px at 300 dpi).
- Check the border on a dark background. Remove stray pixels and holes.

## Die-cut line (cut line)

- Offset the outer silhouette 1 to 2 mm beyond the white border. Smooth the path; fewer nodes cut better.
- Fill internal holes unless the design needs them.
- Save the path as a separate vector or a separate PNG mask. Ask the print shop for its template: line color, layer name, and format differ.
- Keep a minimum width for thin parts (about 2 mm) or the cut tears.

## Sheets

- Gap between stickers: at least 3 mm after the cut line.
- Keep 5 mm from the sheet edge.
- Put ids in a separate proof sheet, not on the print file.

## Color

- Screens show RGB; most printers use CMYK. Bright cyan and saturated greens shift. Ask for a proof when color matters.
- Avoid pure gradients in thin lines; they band.

## Checklist before sending

1. Real dpi stated for every size.
2. White border looks right on a dark background.
3. Cut line separate and closed.
4. No text added after generation.
5. Proof requested for the first order.
