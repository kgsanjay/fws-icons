# FWS Icons

A searchable custom icon gallery with original transparent PNG artwork and traced SVG companions.

**Gallery:** https://kgsanjay.github.io/fws-icons/

## Current collection

The user preferred the original PNG-generated artwork and requested its restoration. The gallery has **110 distinct PNG/SVG pairs**: 100 original icons under `legacy/` and 14 ready master entries, with four shared subjects counted once. The authoritative master list contains **4,176 subjects: 14 complete and 4,162 pending**.

The 20 native SVG revisions (IDs 11–30) have been removed from the gallery and returned to pending. Their files were backed up outside the repository before removal. Attempt counts were preserved. `catalog/work/png-restoration.json` records the recovery; native revision source/audit files are historical.

`catalog/services.txt` holds the authoritative titles in original order; `catalog/original-icon-names.txt` preserves the uploaded list. `catalog/progress.sqlite` is the production queue; `catalog/progress.csv` is its readable export. `legacy/progress.sqlite` is a read-only index of the restored 100 completed icons, not an active queue.

## Run the gallery

```bash
cd /workspace/fws-icons
source /workspace/fws-icons-venv/bin/activate
python tools/build_gallery.py
python -m http.server 8080 --bind 0.0.0.0
```

Serve the repository root so asset/download paths resolve. Search, categories, availability filters, pagination, previews, downloads and custom exports work without a frontend build, CDN or API key. Pending entries have no downloadable artwork. GitHub Pages uses **main → / (root)** with `.nojekyll`; pushes republish after the Pages deployment finishes.

Grid and hero previews use the original PNG artwork. **Original artwork → PNG** preserves that artwork. Size/color/background customization produces SVG exports and PNGs rendered from the traced vector; these can differ slightly from the original PNG. Export dimensions support **16–4096 px per side**, with square locking or independent width/height. Rectangular exports center the artwork without stretching it. Extra padding, single-color mode and light/dark/transparency preview canvases are available. Canvas color does not change the export background. Source files remain unchanged. The preview and settings have separate panels, download actions stay visible, and SVG source is collapsed by default. Filled icons require separately authored artwork; single-color mode preserves the outline design. The next 100 icons remain in the original outline style, per the user’s selection.

The **Download all icons** button downloads `catalog/deliverables/FWS-Icons-All.zip`, rebuilt from distinct ready master and legacy pairs. Complete master batches have separate ZIPs and previews under `catalog/deliverables/`.

## PNG-first production

```bash
python queue.py status
python queue.py next
python queue.py packet BATCH
python queue.py attempt ID
# Generate one transparent PNG with the image tool; inspect it against the originals.
python queue.py accept ID /path/to/generated.png
python queue.py bundle BATCH
```

Commands default to `catalog/`; `--root catalog` can be supplied before the command. Preserve the original collection's detailed charcoal/crimson service-illustration style. Never regenerate completed artwork or reset attempts to bypass validation. Every attempt counts across workflows; stop and report exhausted attempts or unavailable image-generation capability. No paid API fallback is authorized.

Acceptance checks transparency, margins and the presence of both colors. Cleanup removes only alpha=1/255 pixels, archiving the untouched source when cleanup is needed. The PNG is otherwise preserved. VTracer produces filled vector paths in **#202123** and **#C31E25**, with rendered overlap checks against the PNG. It does not embed a raster image. Tracing retains imperfect source contours and cannot guarantee uniform editable strokes; visual review is still required.

Each passing pair is saved immediately, progress is updated, and the gallery/all-icon ZIP is rebuilt. `vectorize BATCH` only backfills missing SVGs without replacing existing ones. `accept-svg` and native validation remain available for explicit native work; PNG-first is the production default.

`tools/import_catalog.py` initializes an empty queue and refuses to overwrite progress; do not rerun it to resume. The optional `run_batches.py` supervisor requires authenticated Codex CLI access and has not been verified here. It is not a persistent background service.

## Validation

```bash
python -m unittest discover -s tests -v
node --check web/app.js
node --check web/export.js
# Gallery served on :8080, Playwright installed, Chromium at /usr/bin/chromium:
python tools/smoke_gallery.py
python tools/test_custom_exports.py
```

Browser checks exercise search, filters, pagination, actual downloads, custom export dimensions/colors/alpha, copying, reset and mobile fit. SVG custom exports use standard unprefixed markup for editor recognition. Direct Figma import still needs a user check. Asset URLs include content versions to avoid stale artwork after deployment.
