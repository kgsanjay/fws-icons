# FWS Icons — gallery and master list

The gallery is a responsive, static website using our custom PNG/SVG artwork. It includes search, suggested categories, pagination, light/dark/transparency previews, an icon detail dialog, SVG source copy, and individual PNG/SVG downloads. Categories are inferred from titles; pending subjects show no fabricated artwork.

## Run the gallery

```bash
cd /workspace/fws-icons
source /workspace/fws-icons-venv/bin/activate
python tools/build_gallery.py
python -m http.server 8080 --bind 0.0.0.0
```

Open the served site in your browser. Serving the repository root is required for image and download paths. Opening index.html directly from disk cannot fetch the JSON index. No frontend build, account, API key, or external CDN is needed. The site has been tested locally; no public deployment or GitHub Pages publication is configured by this change.

## New authoritative list: 4,176 subjects

`catalog/original-icon-names.txt` preserves the uploaded list; `catalog/services.txt` stores the same titles without bracket wrappers, in their original order. `catalog/progress.sqlite` is authoritative for this list. The previous 2,538-entry queue, 100 completed pairs, files and progress remain untouched at the repository root.

The importer reused exactly four completed title matches and recorded their legacy IDs in `catalog/migration.json`. Never assume that the old first 100 all belong to the new list. The gallery's Available icons view combines unique ready titles across both collections; Full master list shows all 4,176 subjects and their availability. Currently 14 master subjects are ready (four reused, ten newly created), leaving 4,162 pending; the combined gallery contains 110 unique available pairs.

Use the explicit queue folder for every new-list command:

```bash
python queue.py --root catalog status
python queue.py --root catalog next
python queue.py --root catalog packet 2
python queue.py --root catalog attempt ID
python queue.py --root catalog accept ID /absolute/path/to/generated.png
python queue.py --root catalog fail ID "reason"
python queue.py --root catalog bundle BATCH
```

Accepted master icons refresh `web/catalog.json` automatically. Run `python tools/build_gallery.py` after manual data changes. New-list output, original images, prompt packets and deliverables live under `catalog/`; old files remain in their existing locations. The first new-list batch is `catalog/deliverables/FWS-Icons-Batch-001.zip` with ten PNG/SVG pairs. PNG alpha cleanup and SVG checks apply to both queues. Never reset attempts or regenerate completed artwork.

`python tools/import_catalog.py INPUT.txt` initializes an empty catalog only and refuses to overwrite existing progress. Do not rerun it to resume. The optional Codex supervisor accepts `--root catalog` and still requires separately available CLI authentication and image-generation capability; it is not a background service and has not been verified here.

## Verification

```bash
python -m unittest discover -s tests -v
node --check web/app.js
# With a server on port 8080, Playwright installed, and Chromium at /usr/bin/chromium:
python tools/smoke_gallery.py
```

The browser checks exercise actual search, availability filters, empty results, modal controls, preview switching, SVG download and mobile overflow. Playwright is optional validation tooling, not a website runtime dependency. Startup does not launch generation. Creating thousands of icons requires resumable active sessions and available image-generation usage.

---

# FWS Icon Factory — Codex project

Contains the user's 2,538 original subjects, organized into 254 delivery batches (last batch has 8). Batches 001–010 contain the first 100 completed icons in PNG and SVG formats; the remaining 2,438 subjects are pending. This is a local Codex queue and supervisor, not a configured paid API worker. Built-in image-generation availability depends on your Codex environment; a ChatGPT login alone does not guarantee it exists there.

## Open in Codex (recommended)
1. Extract this complete folder to a permanent location, e.g. `C:\FWS-Icon-Factory`.
2. Install Python 3.10+ and run `python -m pip install -r requirements.txt` in this folder. On Windows use `py` instead of `python` if needed.
3. Open this folder as a project in Codex. Optionally add one approved style icon named `reference.png`.
4. Paste the complete contents of START-CODEX.txt into Codex. It checks image-generation availability and processes batches, saving after each icon. No API keys are included or required by the queue itself.
5. To resume after interruption, reopen the same folder and use the same prompt. Keep progress.sqlite and output together. Keep the computer awake and connected while running.

## CLI supervisor (optional)
Requires an installed, authenticated Codex CLI with image-generation tools available in non-interactive mode.

```
python run_batches.py
python run_batches.py --all
```

The first command asks Codex to process one pending batch. The second continues through eligible batches. It stops when a Codex call fails or makes no progress. It is NOT an unlimited background service and cannot overcome usage limits. Ctrl+C stops; completed files remain saved. No external messages are sent. If the image generator is unavailable, Codex should stop rather than use an API silently. Configure permissions for the local project as appropriate; the launcher uses workspace-write.

## Queue commands

```
python queue.py status
python queue.py next
python queue.py packet 1
python queue.py attempt 1
python queue.py accept 1 /absolute/path/to/generated.png
python queue.py fail 1 "Reason"
python queue.py vectorize 1  # backfill SVGs for previously completed PNGs
python queue.py bundle 1
```

`packet` prepares jobs and prompt files, not images. `attempt` records each actual generation call; maximum three per icon. `accept` validates and copies the PNG and automatically creates and validates its paired SVG before recording completion; all-white backgrounds and RGB files are rejected. Completion is recorded immediately in SQLite, and progress.csv is refreshed. Original titles and sanitized unique filenames are mapped in the CSV; filename collisions get numeric IDs. Do not run multiple operators against the same folder.

## Deliverables
- output/batch-001/*.png — original individually named transparent icons
- output/batch-001/*.svg — paired scalable vector paths, with the same filenames
- deliverables/FWS-Icons-Batch-001.zip — contains both formats; created only when all batch items and SVG checks pass
- deliverables/FWS-Icons-Batch-001-Preview.jpg — white contact sheet with service labels for review
- progress.csv — readable status; progress.sqlite is authoritative
- work/ — generated prompt packets and notes

Technical checks verify PNG format, square canvas, alpha, visible color presence, absence of large white fills, and margins. They do NOT guarantee exact hex colors, accurate subjects, clean linework or absence of text. Codex must visually inspect each icon. Preview labels are outside the icon PNGs. A request interrupted before its file is saved may need regeneration and consume usage again. Built-in usage limits still apply. No dollar-budget cap or API billing monitor is implemented because no API backend is configured.

## Future API mode
For long unattended production you may later choose an API backend, model, image dimensions and spending cap explicitly. This package does not select a fallback model or make API calls. Do not paste API keys in chat or commit credentials. Existing imagegen CLI skills should be used if API mode is configured in Codex.

Official CLI documentation: https://learn.chatgpt.com/docs/non-interactive-mode

## SVG conversion

Install requirements.txt (Pillow, VTracer, CairoSVG). CairoSVG also needs the native Cairo library (already present in this cloud environment; install your platform Cairo package if missing). No external API or image generation is used for tracing.

`python queue.py vectorize 1` backfills completed PNGs and writes `work/svg-validation-batch-001.json`. Original PNG bytes, queue status and generation attempts are preserved. Re-running replaces SVGs deterministically. Future `accept` calls produce both files; if tracing fails, completion is not recorded. `bundle` refuses missing or invalid SVGs and includes both formats.

SVGs contain real filled vector paths (smoothed curves, with detailed boundary paths as a fallback when smoothing fails fidelity checks) with exactly #202123 and #C31E25, no embedded raster images. Tracing thresholds alpha at 128, maps visible pixels to the two palette colors and removes tiny speckles. It approximates raster edges and does not reconstruct original design objects or editable stroke centerlines. Transparent gaps are preserved. Each SVG is rendered with CairoSVG and must reach at least 95% intersection-over-union against each source color layer. This checks geometry, not subject accuracy or visual quality; inspect both versions. PNGs remain the original generated images and can have slight color variation.

Run `python -m unittest discover -s tests -v` to verify tracing, transparent holes, fidelity rejection and paired queue delivery.

User-approved alpha cleanup: accept removes only pixels with alpha exactly 1/255, preserves every higher-opacity pixel and archives original PNGs by SHA-256 under work/originals/. All original validation still applies. Revalidate saved rejected images after cleanup without resetting generation attempts.

Combined delivery: `deliverables/FWS-Icons-First-100-PNG-SVG.zip` contains 200 icon files in batch folders. `deliverables/FWS-Icons-First-100-Preview.jpg` is the labeled overview. Progress and generation attempt counts remain authoritative in SQLite.
