"""Prepare session 5 source material for visual review, not publication.

Writes rendered pages, raw PDF extraction and image-block metadata to --out.
The raw extraction is NOT a transcript: Persian ligatures, mixed-script order,
line breaks and punctuation require manual correction against the page image.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import pymupdf

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'علوم تشریح سر و گردن/جلسه 5 - گردن/جلسه_پنجم_علوم_تشریح_سر_و_گردن_مهر_1404.pdf'


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='Review working directory')
    parser.add_argument('--scale', type=float, default=1.5)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    source = pymupdf.open(SOURCE)
    inventory = []
    for index, page in enumerate(source):
        number = index + 1
        pix = page.get_pixmap(matrix=pymupdf.Matrix(args.scale, args.scale), alpha=False)
        pix.save(args.out / f'page-{number:02}.png')
        text = page.get_text()
        (args.out / f'page-{number:02}.txt').write_text(text, encoding='utf-8')
        image_blocks = [b for b in page.get_text('dict')['blocks'] if b['type'] == 1]
        inventory.append({'pdf_page': number, 'text_characters': len(text),
                          'image_blocks': [{'bbox': list(b['bbox']), 'width': b['width'],
                                            'height': b['height']} for b in image_blocks]})
    (args.out / 'inventory.json').write_text(json.dumps({'source': str(SOURCE.relative_to(ROOT)),
        'pages': inventory}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{len(source)} pages written to {args.out}; raw text requires visual reconciliation.')


if __name__ == '__main__':
    main()
