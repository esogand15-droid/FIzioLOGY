# Session 6 evidence — reproducible images, no duplicated raster dataset

Bound PDF: `pdf/HumsYar_HeadNeck_Jalase6_FINAL.pdf`

SHA-256: `d05692679a604d622dd43dc6b87ef1d985e968d06df85fd3926f572b80721204`

- `manual_review.json`: record of actual individual viewing of all 60 final pages after the last rebuild, per-page notes and exact JPEG hashes. Not an independent human expert review.
- `source_editorial_review.json`: actual original-page review, cover excluded from transcription; 19 content pages compared with typed text in a separate editorial pass by the same agent.
- `source_text_pairs.json`: 236 preserved typed pieces, not automatically inferred scientific endorsement.
- `reference_editorial_inventory.json`: 33 actually viewed reference pages and inclusion/exclusion decisions; explicitly distinguishes exploratory pages and unviewed rendered pages.
- `machine_manifest.json`: measured PDF, assets, source file hashes and image placements; never marks visual/scientific review complete.
- `layout_trace.json`: build trace for this PDF hash. `page_before` is not necessarily the real starting page of a block.
- `github_delivery.json`, when present: actual commit-pinned GitHub downloads and byte comparisons after push.

The 113 viewed JPEGs (60 final + 20 original + 33 reference) have exact byte hashes and deterministic render recipes recorded, including renderer versions. Their duplicate rasters are deliberately not committed: the repository already contains the source PDFs, final PDF and publication figure assets, and adding another large raster dataset would exceed the session's cumulative artifact budget. No PDF, viewed image content, or recorded hash was altered for this storage choice. A separate from-scratch reproduction of all 113 images matched every recorded JPEG byte hash.

Recreate and validate them outside Git:

```bash
.venv/bin/python headneck/scripts/reproduce_hn06_evidence.py --out .cache/hn06-reproduced
.venv/bin/python headneck/scripts/verify_hn06_final_evidence.py
.venv/bin/python -m unittest discover -s headneck/tests -v
```

`pages/001.jpg` etc. in the inventories are paths relative to the reproduction output directory, not missing committed files. `source/` and `atlas/` are also recreated there. Exact PyMuPDF/Pillow versions and JPEG scale/quality are recorded; a mismatch in a new rendering environment fails explicitly rather than silently accepting different evidence. A successful verifier checks byte continuity and recorded coverage only; it cannot prove reading happened or certify scientific accuracy. New PDF bytes invalidate these records; do not transfer old review flags to a rebuilt PDF.
