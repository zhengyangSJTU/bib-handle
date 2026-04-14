"""Clean and normalize a BibTeX file.

This script removes selected fields, normalizes field values, preserves
organization-style creators written as {{...}}, and removes duplicate entries
by cite key or content fingerprint.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

# User configuration
# Example: INPUT_BIB = Path("references.bib")
INPUT_BIB = Path("paper.bib")

# Example: OUTPUT_BIB = Path("references_cleaned.bib")
OUTPUT_BIB = Path("paper_fixed.bib")

# Fields removed from every entry.
REMOVE_FIELDS_ALWAYS = {"abstract", "keyword", "keywords", "doi", "eprint"}

# Fields wrapped in double braces to preserve capitalization.
# Example: {"title", "journal"}
DOUBLE_BRACED_FIELDS = {"title", "journal", "booktitle", "publisher"}

# Creator-like fields. Organization names written as {{...}} are preserved.
# Example: author = {{CFM International}}
CREATOR_FIELDS = {"author", "editor", "translator"}


def normalize_field_name(name: str) -> str:
    """Normalize a field name for internal matching."""
    return re.sub(r"[\s_-]+", "", name.strip().lower())


def strip_outer_quotes(value: str) -> str:
    """Remove one outer pair of double quotes, if present."""
    value = value.strip()
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1].strip()
    return value


def is_fully_braced(value: str) -> bool:
    """Return True if the whole string is wrapped by one balanced brace layer."""
    value = value.strip()
    if len(value) < 2 or value[0] != "{" or value[-1] != "}":
        return False

    depth = 0
    in_quote = False
    escaped = False

    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue

        if char == "\\":
            escaped = True
            continue

        if in_quote:
            if char == '"':
                in_quote = False
            continue

        if char == '"':
            in_quote = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0 and index != len(value) - 1:
                return False

    return depth == 0 and not in_quote and not escaped


def strip_outer_braces(value: str) -> str:
    """Repeatedly remove one full outer brace layer."""
    value = value.strip()
    while is_fully_braced(value):
        value = value[1:-1].strip()
    return value


def is_whole_double_braced(value: str) -> bool:
    """Return True for organization-style values such as {{CFM International}}."""
    value = strip_outer_quotes(value)

    if len(value) < 4:
        return False
    if not (value.startswith("{{") and value.endswith("}}")):
        return False
    if not is_fully_braced(value):
        return False

    inner = value[1:-1].strip()
    return is_fully_braced(inner)


def split_top_level_fields(body: str) -> list[str]:
    """Split entry fields by top-level commas only."""
    fields: list[str] = []
    start = 0
    depth = 0
    in_quote = False
    escaped = False

    for index, char in enumerate(body):
        if escaped:
            escaped = False
            continue

        if char == "\\":
            escaped = True
            continue

        if in_quote:
            if char == '"':
                in_quote = False
            continue

        if char == '"':
            in_quote = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
        elif char == "," and depth == 0:
            part = body[start:index].strip()
            if part:
                fields.append(part)
            start = index + 1

    tail = body[start:].strip()
    if tail:
        fields.append(tail)

    return fields


def find_entry_end(source: str, start: int, open_char: str, close_char: str) -> int:
    """Find the closing position of a BibTeX entry."""
    depth = 0
    in_quote = False
    escaped = False

    for index in range(start, len(source)):
        char = source[index]

        if escaped:
            escaped = False
            continue

        if char == "\\":
            escaped = True
            continue

        if in_quote:
            if char == '"':
                in_quote = False
            continue

        if char == '"':
            in_quote = True
        elif char == open_char:
            depth += 1
        elif char == close_char:
            depth -= 1
            if depth == 0:
                return index

    return -1


def find_key_end(
        source: str,
        start: int,
        end: int,
        open_char: str,
        close_char: str,
) -> int:
    """Find the first top-level comma after the cite key."""
    depth = 1
    in_quote = False
    escaped = False

    for index in range(start, end + 1):
        char = source[index]

        if escaped:
            escaped = False
            continue

        if char == "\\":
            escaped = True
            continue

        if in_quote:
            if char == '"':
                in_quote = False
            continue

        if char == '"':
            in_quote = True
        elif char == open_char:
            depth += 1
        elif char == close_char:
            depth -= 1
        elif char == "," and depth == 1:
            return index

    return -1


def should_drop_field(entry_type: str, field_name: str) -> bool:
    """Return True if a field should be removed from the output."""
    field_name = normalize_field_name(field_name)
    entry_type = entry_type.strip().lower()

    if field_name in REMOVE_FIELDS_ALWAYS:
        return True

    # url / urldate only stay in @online entries.
    if field_name == "url" and entry_type != "online":
        return True

    if field_name == "urldate" and entry_type != "online":
        return True

    return False


def clean_field_value(field_name: str, value: str) -> str:
    """Normalize a field value and apply the required brace style."""
    field_name_normalized = normalize_field_name(field_name)
    value = value.strip()

    # Preserve organization-style creators such as {{NASA}}.
    if field_name_normalized in CREATOR_FIELDS and is_whole_double_braced(value):
        return strip_outer_quotes(value)

    value = strip_outer_quotes(value)
    content = strip_outer_braces(value)

    if field_name_normalized in DOUBLE_BRACED_FIELDS:
        return f"{{{{{content}}}}}"

    return f"{{{content}}}"


def raw_value_content(value: str) -> str:
    """Extract the logical content of a field value."""
    value = strip_outer_quotes(value)
    value = strip_outer_braces(value)
    return value.strip()


def normalize_text_for_fingerprint(text: str) -> str:
    """Normalize text for duplicate detection."""
    text = text.strip().lower()
    text = re.sub(r"[{}\\]", "", text)
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[^\w\u4e00-\u9fff]+", "", text)
    return text


def first_creator_token(field_value: str) -> str:
    """Extract the first creator token for fingerprinting."""
    content = raw_value_content(field_value)
    parts = re.split(r"\s+\band\b\s+", content, maxsplit=1, flags=re.I)
    return normalize_text_for_fingerprint(parts[0]) if parts else ""


def year_from_fields(field_map: dict[str, str]) -> str:
    """Extract a four-digit year from year or date."""
    if "year" in field_map:
        match = re.search(r"\d{4}", raw_value_content(field_map["year"]))
        if match:
            return match.group(0)

    if "date" in field_map:
        match = re.search(r"\d{4}", raw_value_content(field_map["date"]))
        if match:
            return match.group(0)

    return ""


def build_fingerprint(
        entry_type: str,
        field_map: dict[str, str],
) -> Optional[tuple[str, ...]]:
    """Build a duplicate-detection fingerprint.

    Priority:
    1. DOI
    2. title + year/date + first creator
    3. title + year/date
    4. title
    """
    del entry_type  # Reserved for future rules.

    doi = field_map.get("doi")
    if doi:
        doi_normalized = normalize_text_for_fingerprint(raw_value_content(doi))
        if doi_normalized:
            return ("doi", doi_normalized)

    title = normalize_text_for_fingerprint(raw_value_content(field_map.get("title", "")))
    year = year_from_fields(field_map)

    creator = ""
    for key in ("author", "editor", "translator"):
        if key in field_map:
            creator = first_creator_token(field_map[key])
            if creator:
                break

    if title and year and creator:
        return ("tyc", title, year, creator)

    if title and year:
        return ("ty", title, year)

    if title:
        return ("t", title)

    return None


def process_entry(entry_text: str) -> tuple[Optional[str], str, Optional[tuple[str, ...]]]:
    """Parse, normalize, and rebuild one BibTeX entry."""
    match = re.match(r"\s*@(\w+)\s*([({])", entry_text)
    if not match:
        return None, entry_text, None

    entry_type = match.group(1)
    open_char = match.group(2)
    close_char = "}" if open_char == "{" else ")"

    open_pos = entry_text.find(open_char, match.end() - 1)
    close_pos = find_entry_end(entry_text, open_pos, open_char, close_char)
    if close_pos == -1:
        return None, entry_text, None

    key_pos = find_key_end(entry_text, open_pos + 1, close_pos, open_char, close_char)
    if key_pos == -1:
        return None, entry_text, None

    cite_key = entry_text[open_pos + 1:key_pos].strip()
    body = entry_text[key_pos + 1:close_pos].strip()

    raw_fields = split_top_level_fields(body)
    field_map: dict[str, str] = {}
    ordered_fields: list[tuple[str, str]] = []

    for field in raw_fields:
        if "=" not in field:
            continue
        name, value = field.split("=", 1)
        raw_name = name.strip()
        cleaned_value = value.strip()
        field_map[normalize_field_name(raw_name)] = cleaned_value
        ordered_fields.append((raw_name, cleaned_value))

    fingerprint = build_fingerprint(entry_type, field_map)

    new_fields = []
    for raw_name, value in ordered_fields:
        if should_drop_field(entry_type, raw_name):
            continue
        new_value = clean_field_value(raw_name, value)
        new_fields.append(f"  {raw_name} = {new_value},")

    lines = [f"@{entry_type}{open_char}{cite_key},"]
    lines.extend(new_fields)
    lines.append(close_char)

    return cite_key, "\n".join(lines), fingerprint


def clean_bib_file(input_path: Path, output_path: Path) -> None:
    """Clean a BibTeX file and write the normalized result."""
    text = input_path.read_text(encoding="utf-8")

    # Scan only entries that start at the beginning of a line.
    entry_head_pattern = re.compile(r"(?m)^[ \t]*@(\w+)\s*([({])")

    seen_keys: set[str] = set()
    seen_fingerprints: set[tuple[str, ...]] = set()

    duplicate_keys: list[str] = []
    duplicate_contents: list[str] = []
    entries_out: list[str] = []

    matches = list(entry_head_pattern.finditer(text))
    index = 0

    while index < len(matches):
        match = matches[index]
        start = match.start()

        open_char = match.group(2)
        close_char = "}" if open_char == "{" else ")"
        open_pos = match.end() - 1
        end_pos = find_entry_end(text, open_pos, open_char, close_char)

        # Skip malformed entries and continue scanning.
        if end_pos == -1:
            index += 1
            continue

        entry_text = text[start: end_pos + 1]
        cite_key, fixed_entry, fingerprint = process_entry(entry_text)

        if cite_key is None:
            index += 1
            continue

        if cite_key in seen_keys:
            duplicate_keys.append(cite_key)
        elif fingerprint is not None and fingerprint in seen_fingerprints:
            duplicate_contents.append(cite_key)
        else:
            seen_keys.add(cite_key)
            if fingerprint is not None:
                seen_fingerprints.add(fingerprint)
            entries_out.append(fixed_entry.strip())

        index += 1

    # Output format:
    # - no blank line at the top
    # - exactly one blank line between entries
    # - one trailing newline at the end of the file
    fixed_text = "\n\n".join(entries_out) + "\n"
    output_path.write_text(fixed_text, encoding="utf-8")

    print("done:", output_path)

    if duplicate_keys:
        print("duplicate keys removed:")
        for key in duplicate_keys:
            print("  -", key)
    else:
        print("no duplicate keys found")

    if duplicate_contents:
        print("duplicate contents removed:")
        for key in duplicate_contents:
            print("  -", key)
    else:
        print("no duplicate contents found")


def main() -> None:
    """Run the cleaner with the current configuration."""
    if not INPUT_BIB.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_BIB}")

    clean_bib_file(INPUT_BIB, OUTPUT_BIB)


if __name__ == "__main__":
    main()
