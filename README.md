# FWS Icons

A searchable custom icon gallery with native SVG sources and matching transparent PNG exports.

**Gallery:** https://kgsanjay.github.io/fws-icons/

## Current collection

The master list contains **4,176 subjects**. **20 native SVG/PNG pairs** are complete (master IDs 11–30); **4,156 subjects** are pending.

At the user's request, raster-generated/traced icons and their old downloads, previews, original-image copies, and obsolete queue were removed from the current repository. Four reused traces and the first ten traced master icons were returned to pending for native redesign. Existing authoring attempt counts were preserved. The remaining completed SVG-first artwork was kept intact.

`catalog/services.txt` holds the authoritative titles in original order. `catalog/original-icon-names.txt` preserves the uploaded list. `catalog/progress.sqlite` is authoritative; `catalog/progress.csv` is its readable export.

## Run the gallery

```bash
cd /workspace/fws-icons
source /workspace/fws-icons-venv/bin/activate
python tools/build_gallery.py
python -m http.server 8080 --bind 0.0.0.0
```

Serve the repository root so image and download paths resolve. The gallery has search, categories, availability filters, pagination, SVG/PNG preview, and individual downloads. Pending entries have no downloadable artwork. There is no frontend build, external CDN, API key, or account requirement.

GitHub Pages uses **main → / (root)** with `.nojekyll`. Pushes republish after the Pages deployment finishes.

## Custom exports

Open a ready icon to choose **16–4096 px**, primary/accent colors, and a transparent or solid background. The preview, copied SVG and downloads use those settings. SVG preserves its vector paths and viewBox; PNG is rendered from the customized SVG. Stroke and fill colors are supported. Source files stay unchanged; separate original downloads remain available.

The **Download all icons** button downloads `catalog/deliverables/FWS-Native-Icons-All.zip`, rebuilt from current ready pairs whenever the gallery index is refreshed. Completed batches have separate ZIPs and previews under `catalog/deliverables/`.

## SVG-first production

```bash
python queue.py status
python queue.py next
python queue.py packet BATCH
python queue.py attempt ID
# Author and visually inspect catalog/work/batch-NNN/ID.svg
python queue.py accept-svg ID catalog/work/batch-NNN/ID.svg --size 1024
python queue.py bundle BATCH
```

Commands default to `catalog/`; `--root catalog` can also be supplied before the command. New master icons require native SVG-first authoring. PNG-first acceptance and retracing are blocked. Never regenerate completed artwork or reset attempts to bypass validation.

Use a square `viewBox="0 0 128 128"`, `fill="none"`, consistent 3-unit strokes, round caps and joins, and only charcoal **#202123** / crimson **#C31E25**. Use simple geometry with generous margins, aligned elements and clear joins. Avoid touching contours, text, logos, scripts, CSS, transforms, external resources, and raster embedding. Inspect at small and large sizes; numerical stroke consistency alone does not prove optical quality.

Acceptance validates native geometry and strokes, exports a 1024×1024 transparent PNG, checks colors/margins, and verifies the PNG is an exact SVG render. It saves each passing pair immediately, updates progress and rebuilds the gallery and all-icon ZIP. Source authoring and visual review take most of the time; PNG export is automatic and does not use an image-generation service.

`tools/import_catalog.py` initializes an empty queue only and refuses to overwrite progress. It no longer reuses retired legacy artwork. Do not rerun it to resume.

The optional `run_batches.py` supervisor requires separately available, authenticated Codex CLI access and has not been verified here. It is not a persistent background service.

## Validation

```bash
python -m unittest discover -s tests -v
node --check web/app.js
node --check web/export.js
# With the gallery served on port 8080, Playwright installed and Chromium at /usr/bin/chromium:
python tools/smoke_gallery.py
python tools/test_custom_exports.py
```

Browser checks exercise search, filters, pagination, modal controls, previews, real downloads, custom export dimensions/colors/alpha, copying, reset and mobile fit. Playwright is optional test tooling, not a website runtime dependency.

## Reference-style review revision

The user authorized revising all 20 completed icons to follow the archived original service-illustration reference: fuller compositions, subject-specific detail, stronger 3-unit strokes, charcoal structure and crimson functional accents. Native SVG sources and matching PNGs remain the workflow. This set is awaiting the user’s visual assessment; numerical validation does not certify a style match. The revision source and audit record are in `catalog/work/reference-revision/`; queue status remains 20 complete.

Gallery asset URLs include content-version keys so revised files are requested after deployment. `catalog/deliverables/Reference-Style-20-Preview.png` is the current review sheet.

SVG exports use standard unprefixed `<svg xmlns="http://www.w3.org/2000/svg">` markup for editor file import and clipboard recognition. Original files, custom downloads, and Copy SVG all use this serialization. Namespace normalization preserves editable paths, strokes and rendered artwork. Browser/render regression tests cover this format; direct Figma import still requires a user check.
