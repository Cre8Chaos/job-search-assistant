# Pipeline Table Format

The workspace `data/pipeline.md` is the master tracking table. `scripts/pipeline.py`
creates and edits it; skills read it. Header:

```markdown
# Job Pipeline

| Company | Role | Grade | Status | Date Found | Job File |
|---|---|---|---|---|---|
```

**Statuses:** `New` → `Evaluated` → `Tailored` → `Ready` → `Applied` (or `Skip`).
**Grades:** `A` (strong) · `B` (good, minor gaps) · `C` (borderline) · `D`/`F` (skip).

Add a row:
```bash
python scripts/pipeline.py add "<Company>" "<Role>" "<relative/path/to/job.md>"
```
Update a row:
```bash
python scripts/pipeline.py update "<Company>" "<Role>" --grade A
python scripts/pipeline.py update "<Company>" "<Role>" --status Applied --date YYYY-MM-DD
```
