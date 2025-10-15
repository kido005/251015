# Car Picker Quiz App Design

## Goals
- Browser‑based quiz that shows a random car image and asks the user to identify make, model, and year.
- Support three quiz modes (Make only, Make + Model, Make + Model + Year) with partial scoring.
- Display 10 answer choices per question, track score over a fixed 10‑question session, and enforce a 10‑minute time limit.
- Leverage the existing `car_picker/data` image set whose filenames encode metadata per the picture-scraper README.
- Cache parsed metadata and generated thumbnails for performance.

## Technology Choices
- **Streamlit** for rapid UI development, stateful sessions, and simple browser deployment.
- **Python 3.9+** (align with Streamlit support).
- **Pillow** for image handling and thumbnail generation.
- **Pandas** (optional) for easier data manipulation when building the index.
- **Imagehash** (optional future enhancement) for duplicate detection; not required initially.
- **Filesystem cache** stored inside `.cache/` and thumbnails inside `.thumbnails/`.

## High-Level Architecture
```
car_picker/
├── app.py              # Streamlit entry point
├── core/
│   ├── parser.py       # Filename parsing & validation
│   ├── indexer.py      # Dataset indexing, caching, thumbnail generation
│   ├── options.py      # Answer option generation logic
│   ├── engine.py       # Quiz session management & scoring
│   └── timer.py        # Countdown helper (10-minute session)
├── DESIGN.md           # This document
├── requirements.txt    # Python dependencies
├── .cache/
│   └── index.json      # Cached metadata (auto-created)
├── .thumbnails/        # Cached resized images (auto-created)
└── data/               # Original car images (already provided)
```

### Data Flow
1. **Initialization**
   - On first run, `indexer` scans `data/`, parses filenames via `parser`, and stores a list of `CarImage` records (`id`, `path`, `make`, `model`, `year`, `specs`).
   - Index serialized to `.cache/index.json` with a hash of relevant file metadata to detect when rescanning is needed.
   - `indexer` optionally creates thumbnails (longest side ≈512 px) stored in `.thumbnails/` for faster rendering.
2. **Question Generation**
   - `engine` selects a candidate record not yet used in the current session and asks `options` for 9 distractors appropriate for the current mode.
   - `options` prioritizes semantically similar distractors (same make, different model/year) and fills remaining slots with random unique picks.
3. **Gameplay**
   - Streamlit UI pulls a question, displays the image, answer buttons, timer, and score.
   - When the user answers, `engine` computes full/partial credit and stores feedback.
4. **Session End**
   - After 10 questions or when the 10-minute timer elapses, the UI displays final score and per-question breakdown.

## Key Components

### `parser.py`
- `parse_filename(path: Path) -> CarImage | None`
- Validates underscore-separated tokens (expect 17 including the random ID fragment).
- Returns dataclass with attributes (`make`, `model`, `year`, `specs`, `id`, `path`).
- Gracefully skips invalid files; logs counts for visibility.

### `indexer.py`
- `build_index(data_dir: Path, cache_dir: Path, thumb_dir: Path) -> DatasetIndex`
- Loads `.cache/index.json` if present and consistent.
- Otherwise scans `data_dir`, uses `parser`, writes JSON cache.
- `ensure_thumbnail(car: CarImage) -> Path` generates/resolves thumbnails.
- Provides helper filter functions (e.g., by make/model).

### `options.py`
- `generate_choices(correct: CarImage, index: DatasetIndex, mode: QuizMode, k: int=10) -> Choices`
- Ensures the correct answer is included and returns metadata for UI.
- Strategy:
  - Gather candidates sharing make (different model/year) and same make/model different year depending on mode.
  - Shuffle and pad up to `k-1` with random unique entries.
  - Each option carries display label adapted to mode (e.g., `Make` only vs `Make Model Year`).

### `engine.py`
- Defines `QuizMode` enum (`MAKE`, `MAKE_MODEL`, `MAKE_MODEL_YEAR`).
- `QuizState` dataclass holds session stats (score, partial credit, current question number, used IDs, answers list).
- `compute_score(correct: CarImage, guess: Answer, mode: QuizMode) -> ScoreDetail`:
  - Base points: 1.0 for full match.
  - Partial scoring rules:
    - `MAKE`: 1.0 if make matches (only requirement).
    - `MAKE_MODEL`: 0.5 for make, +0.5 for model.
    - `MAKE_MODEL_YEAR`: 0.3 for make, +0.4 for model, +0.3 for year.
- `next_question(state, mode)` handles question sequencing and ensures 10 unique prompts.

### `timer.py`
- Wrapper for storing session start time in `st.session_state`.
- Exposes `remaining_time()` (seconds) and `expired()` boolean for UI to disable answering when time runs out.

### `app.py` (Streamlit UI)
- Sidebar controls:
  - Select quiz mode.
  - Show instructions.
- Main panel:
  - Timer display + current question out of 10.
  - Image (thumbnail).
  - Ten buttons for answer choices.
  - Feedback area for previous question (correct answer, partial credit info).
  - Score summary (current score, accuracy, partial breakdown).
- Flow control:
  - Session resets via “Restart Quiz” button (clears state, restarts timer).
  - Automatically stops after 10 questions or when timer hits zero, showing results table.

## Constraints & Assumptions
- Image dataset may include duplicates and interior shots; allowed per user direction.
- Expect thousands of images; index and thumbnail caching required for acceptable load times.
- Streamlit runs as local app; no authentication/account system.
- Randomness should be reproducible within session (seeded per session state).
- Works offline; uses local files only.

## Testing Strategy
- Unit tests (optional later) for parser, option generation, and scoring – can be simple pytest cases.
- Manual QA via Streamlit:
  - Verify each mode’s display labels and scoring.
  - Confirm timer stops interaction at 10 minutes.
  - Confirm 10 questions per session and restart works.

## Future Enhancements
- Integrate duplicate detection/heavier filtering (e.g., remove interior shots).
- Add hint system (e.g., reveal make) or streak multipliers.
- Persist historical scores to JSON/CSV.
- Support keyboard shortcuts for faster play.

