"""Check PDF xref, streams and embedded TrueType fonts without recovery mode.

Usage: python headneck/scripts/verify_pdf_integrity.py pdf/HumsYar_HeadNeck_Jalase3.pdf
This checks file integrity, not scientific accuracy or visual layout.
"""
import io
import sys
from pathlib import Path

from fontTools.ttLib import TTFont
from pypdf import PdfReader


def verify(path: Path) -> None:
    reader = PdfReader(str(path), strict=True)
    font_ids = set()
    for page in reader.pages:
        content = page.get_contents()
        if content is not None:
            content.get_data()  # decode the content stream
        for ref in page.get('/Resources', {}).get('/Font', {}).values():
            font = ref.get_object()
            descriptor = font.get('/FontDescriptor')
            if not descriptor:
                continue
            descriptor = descriptor.get_object()
            stream = descriptor.get('/FontFile2')
            if not stream or stream.idnum in font_ids:
                continue
            font_ids.add(stream.idnum)
            data = stream.get_object().get_data()
            if not data:
                raise ValueError('empty embedded TrueType font')
            tt = TTFont(io.BytesIO(data), lazy=False)
            # Subset fonts may legitimately have no Unicode cmap; the PDF
            # encoding and ToUnicode map provide the character mapping.
            if 'glyf' not in tt or 'cmap' not in tt or len(tt.getGlyphOrder()) < 2:
                raise ValueError('invalid embedded TrueType font')
            tt.close()
    if not reader.pages or not font_ids:
        raise ValueError('no pages or embedded TrueType fonts')
    print(f'{path}: {len(reader.pages)} pages, {len(font_ids)} embedded fonts OK')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    for name in sys.argv[1:]:
        verify(Path(name))
