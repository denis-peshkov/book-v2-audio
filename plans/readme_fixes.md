# README Fixes Needed

## Issues in ALL 4 READMEs (EN/RU/JA/ZH)

### 1. `logo.png` doesn't exist
- Referenced in project structure tree
- Referenced in PyInstaller `--add-data "logo.png:."` (line 91 in all READMEs)
- Referenced in spec file description: "включает logo.png"
- File `logo.png` is missing from the workspace

### 2. `LICENSE` file doesn't exist
- Badge `[![License: MIT]` links to `LICENSE` — file doesn't exist

### 3. Output path is wrong
- README says: `~/audiobooks/<book_title>/<book_title>.mp3` (subdirectory)
- Actual code ([`pipeline.py:249`](src/core/pipeline.py:249)): `output_dir / output_filename` → `~/audiobooks/<book_title>.mp3` (no subdirectory)

### 4. `--hidden-import tomli` is stale
- We replaced `tomli` with stdlib `tomllib` — no `import tomli` anywhere
- Remove this hidden-import from all 4 READMEs

### 5. `--hidden-import structlog` — never imported in code
- In `pyproject.toml` as dependency but no source file does `import structlog`
- `logger.py` only uses standard `logging`
- Safe to remove from hidden-imports

### 6. `--hidden-import lxml` — never imported in code
- In `pyproject.toml` as dependency but no source file does `import lxml`  
- `fb2_parser.py` uses `defusedxml.ElementTree`
- Safe to remove from hidden-imports
