# harry-potter

harry-potter is a terminal-first exploration game set in the wizarding world from Harry Potter's perspective.

Wander through Hogwarts corridors, tower rooms, classroom wings, the grounds, Hogsmeade, and Diagon Alley while gathering rumors, talking with familiar faces, and letting the map quietly open up. The tone aims for book-style magical atmosphere rather than combat-heavy RPG structure: curious, watchful, occasionally tense, and full of small hidden pressures.

Current highlights:

- authored Hogwarts, Hogsmeade, and Diagon Alley locations with internal sub-areas
- canonical and lore-compatible non-canonical NPCs with memory and personal troubles
- rumors, favors, small missions, and faction drift
- optional AI-generated magical expansion regions with local fallback generation
- richer terminal presentation with `rich`
- save and autosave support

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

Optional environment variables:

```env
OPENAI_API_KEY=your_key_here
OPENAI_TEXT_MODEL=gpt-4.1-mini
TYPEWRITER_DELAY=0.005
REDUCED_MOTION=false
```

## Run

```bash
python game.py
```

or:

```bash
python -m hogwarts_game
```

## Commands

- `look`
- `hint`
- `areas`
- `inspect <thing>`
- `listen`
- `people`
- `talk <name>`
- `ask <name> about <topic>`
- `go <area>`
- `enter <shop>`
- `leave`
- `move <place>`
- `travel <place>`
- `where`
- `map`
- `rumors`
- `journal`
- `menu`
- `save`
- `load`
- `help`
- `quit`

## Notes

- The world stays playable without `OPENAI_API_KEY` using local fallback narration and fallback dynamic region generation.
- Dynamic regions, NPC memory, rumors, missions, and discovered locations persist in saves.
