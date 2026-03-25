# Tarot card assets

This directory contains the versioned, static tarot catalog base data.

## Files
- `cards.base.json`: technical card metadata (language-neutral)
- localized card text files are in `app/data/i18n/` as `cards.<locale>.json`

## Conventions
- `card_no`
  - Numeric card identifier `1..78`
  - Primary key for joining `cards.base.json` with `cards.<locale>.json`
  - Guarantees stable lookup from localized content to `image_path`
- `id`
  - Major: `major_{NN}_{slug}` where `NN` is 2-digit (00-21), e.g. `major_00_the_fool`
  - Minor: `minor_{suit}_{rank}`, e.g. `minor_wands_ace`, `minor_cups_ten`, `minor_swords_queen`
- `image_path`
  - Relative to `app/static/`
  - Major: `cards/major/{NN}_{slug}.webp`
  - Minor: `cards/minor/{suit}/{rank}.webp`

## Localized card files
- `cards.<locale>.json` uses `cards: []`
- each item must contain:
  - `card_no` (number, required)
  - `id` (string, required, must match base card with same `card_no`)
  - `name`, `keywords`, `meaning_upright`, `meaning_reversed`

