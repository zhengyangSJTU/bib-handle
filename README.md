# BibTeX Cleaner

A small Python script for cleaning and normalizing `.bib` files.

## What it does

- Removes fields you do not want to keep
- Wraps selected fields in double braces `{{...}}`
- Formats the output file in a consistent style
- Preserves organization-style creators with double braces, such as `author = {{CFM International}}`

## Quick start

1. Put the BibTeX file you want to process in the same directory as the script.
   - By default, the script reads `paper.bib`
   - By default, the cleaned output is written to `paper_fixed.bib`
2. Check the configuration section at the top of the script and adjust it if needed.
3. Run the script:

```bash
python3 -u bib_handle.py
```

## Configuration

The main settings are defined near the top of the script.

### 1. Input and output files

Use these variables to set the input and output file names:

```python
INPUT_BIB = Path("paper.bib")
OUTPUT_BIB = Path("paper_fixed.bib")
```

### 2. Fields to remove

Use `REMOVE_FIELDS_ALWAYS` to define fields that should always be removed.

```python
REMOVE_FIELDS_ALWAYS = {"abstract", "keyword", "keywords", "doi", "eprint"}
```

Before:

```bibtex
@article{sample,
  title = {Example Title},
  doi = {10.1000/test},
  note = {internal note}
}
```

After:

```bibtex
@article{sample,
  title = {{Example Title}},
}
```

### 3. Fields wrapped in double braces

Use `DOUBLE_BRACED_FIELDS` to control which fields should be written as `{{...}}`.

```python
DOUBLE_BRACED_FIELDS = {"title", "journal", "booktitle", "publisher"}
```

Before:

```bibtex
title = {CFD Study of NH3 Spray}
```

After:

```bibtex
title = {{CFD Study of NH3 Spray}}
```

### 4. Organization-style creators

Use `CREATOR_FIELDS` to define creator-like fields where organization names may appear.
Organization names should use double braces in the BibTeX file.

```python
CREATOR_FIELDS = {"author", "editor", "translator"}
```

Example input:

```bibtex
author = {{CFM International}}
```

Output:

```bibtex
author = {{CFM International}}
```

This keeps the organization name protected as a single creator.

## Notes

- Do **not** wrap normal personal author names in double braces, such as `author = {{John Smith and Jane Doe}}`.
- This may break bibliography formatting. For example, styles that should shorten long author lists to `et al.` may instead print all authors.
- For Chinese authors, it may also produce incorrect output such as `张三 and 李四 and 王五` instead of the expected formatted result.
- Double braces in `author` are intended for organization names only, for example `author = {{CFM International}}`.
