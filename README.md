# BibTeX Cleaner

A small Python script for cleaning and normalizing `.bib` files.

## What it does

- Removes selected fields such as `abstract`, `keywords`, `doi`, and `eprint`
- Keeps `url` and `urldate` only for `@online` entries
- Preserves organization-style creators such as `{{CFM International}}`
- Normalizes braces for common fields
- Removes duplicate entries by cite key or content fingerprint
- Writes output with consistent blank-line spacing

## Quick start

1. Put your input file in the same folder as the script.
2. Edit the configuration section at the top of the script if needed.
3. Run:

```bash
python bib_cleaner.py
```

## Default file names

- Input: `paper.bib`
- Output: `paper_fixed.bib`

## Notes

- The script is designed for BibTeX-style entries that begin at the start of a line.
- For creator fields such as `author`, `editor`, and `translator`, double-braced organization names are preserved.
