import csv
from dictdiffer import diff
import json
import hashlib
import math
import hashlib


def load_csv(fp, key=None, dialect=None):
    if dialect is None and fp.seekable():
        # Peek at first 1MB to sniff the delimiter and other dialect details
        peek = fp.read(1024**2)
        fp.seek(0)
        try:
            dialect = csv.Sniffer().sniff(peek, delimiters=",\t;")
        except csv.Error:
            # Oh well, we tried. Fallback to the default.
            pass
    fp = csv.reader(fp, dialect=(dialect or "excel"))
    try:
        headings = next(fp)
    except StopIteration:
        return {}
    if len(headings) != len(set(headings)):
        raise ValueError("CSV header contains duplicate field names")
    rows = []
    for line_number, line in enumerate(fp, 2):
        if len(line) < len(headings):
            raise ValueError(
                f"Row {line_number} has {len(line)} fields; expected at least {len(headings)}"
            )
        if len(line) > len(headings):
            extra_fields = line[len(headings):]
            if any(extra_fields):
                raise ValueError(
                    f"Row {line_number} has {len(line)} fields; expected at most {len(headings)}"
                )
            line = line[:len(headings)]
        rows.append(dict(zip(headings, line)))
    if key:
        def keyfn(row):
            value = row.get(key)
            if value is None or value == "":
                raise ValueError(f"Key column {key!r} contains a null value")
            return value
    else:
        keyfn = lambda r: hashlib.sha1(
            json.dumps(r, sort_keys=True).encode("utf8")
        ).hexdigest()
    indexed = {}
    for row in rows:
        row_key = keyfn(row)
        if row_key in indexed:
            raise ValueError(f"Duplicate key value: {row_key!r}")
        indexed[row_key] = row
    return indexed


def load_json(fp, key=None):
    raw_list = json.load(fp)
    if not isinstance(raw_list, list) or not all(
        isinstance(item, dict) for item in raw_list
    ):
        raise ValueError("JSON input must be an array of objects")
    common_keys = set()
    for item in raw_list:
        common_keys.update(item.keys())
    if key:
        def keyfn(row):
            if key not in row or row[key] is None or row[key] == "":
                raise ValueError(f"Key column {key!r} contains a null value")
            return row[key]
    else:
        keyfn = lambda r: hashlib.sha1(
            json.dumps(r, sort_keys=True).encode("utf8")
        ).hexdigest()
    indexed = {}
    for row in raw_list:
        if key and key in row and isinstance(row[key], (dict, list)):
            raise ValueError(f"Key column {key!r} must contain a scalar value")
        if key and key in row and isinstance(row[key], float) and not math.isfinite(row[key]):
            raise ValueError(f"Key column {key!r} must contain a finite value")
        row = _simplify_json_row(row, common_keys)
        row_key = keyfn(row)
        if row_key in indexed:
            raise ValueError(f"Duplicate key value: {row_key!r}")
        indexed[row_key] = row
    return indexed


def _simplify_json_row(r, common_keys):
    # Convert list/dict values into JSON serialized strings
    for key, value in r.items():
        if isinstance(value, (dict, tuple, list)):
            r[key] = json.dumps(value)
    for key in common_keys:
        if key not in r:
            r[key] = None
    return r


def compare(previous, current, show_unchanged=False):
    result = {
        "added": [],
        "removed": [],
        "changed": [],
        "columns_added": [],
        "columns_removed": [],
    }
    # If both dicts are empty, return early to avoid StopIteration on next()
    if not previous and not current:
        return result

    # Handle edge case: if only one dict is empty, all rows are added or removed
    if not previous:
        result["added"] = list(current.values())
        return result
    if not current:
        result["removed"] = list(previous.values())
        return result

    # Have the columns changed?
    previous_columns = set(next(iter(previous.values())).keys())
    current_columns = set(next(iter(current.values())).keys())
    ignore_columns = None
    if previous_columns != current_columns:
        result["columns_added"] = [
            c for c in current_columns if c not in previous_columns
        ]
        result["columns_removed"] = [
            c for c in previous_columns if c not in current_columns
        ]
        ignore_columns = current_columns.symmetric_difference(previous_columns)
    # Have any rows been removed or added?
    removed = [id for id in previous if id not in current]
    added = [id for id in current if id not in previous]
    # How about changed?
    removed_or_added = set(removed) | set(added)
    potential_changes = [id for id in current if id not in removed_or_added]
    changed = [id for id in potential_changes if current[id] != previous[id]]
    if added:
        result["added"] = [current[id] for id in added]
    if removed:
        result["removed"] = [previous[id] for id in removed]
    if changed:
        for id in changed:
            diffs = list(diff(previous[id], current[id], ignore=ignore_columns))
            if diffs:
                changes = {
                    "key": id,
                    "changes": {
                        # field can be a list if id contained '.' - #7
                        field[0] if isinstance(field, list) else field: [
                            prev_value,
                            current_value,
                        ]
                        for _, field, (prev_value, current_value) in diffs
                    },
                }
                if show_unchanged:
                    changes["unchanged"] = {
                        field: value
                        for field, value in previous[id].items()
                        if field not in changes["changes"] and field != "id"
                    }
                result["changed"].append(changes)
    return result


def human_text(result, key=None, singular=None, plural=None, current=None, extras=None):
    singular = singular or "row"
    plural = plural or "rows"
    title = []
    summary = []
    # Determine if we should show section headers
    # Show headers if we have multiple distinct sections (columns, changes, adds, removes)
    section_keys = ["columns_changed", "changed", "added", "removed"]
    non_empty_sections = sum(1 for key in section_keys if result.get(key))
    # Also include columns if any were added or removed
    if result["columns_added"] or result["columns_removed"]:
        show_headers = non_empty_sections > 0
    else:
        show_headers = non_empty_sections > 1
    if result["columns_added"]:
        fragment = "{} {} added".format(
            len(result["columns_added"]),
            "column" if len(result["columns_added"]) == 1 else "columns",
        )
        title.append(fragment)
        summary.extend(
            [fragment, ""]
            + ["  {}".format(c) for c in sorted(result["columns_added"])]
            + [""]
        )
    if result["columns_removed"]:
        fragment = "{} {} removed".format(
            len(result["columns_removed"]),
            "column" if len(result["columns_removed"]) == 1 else "columns",
        )
        title.append(fragment)
        summary.extend(
            [fragment, ""]
            + ["  {}".format(c) for c in sorted(result["columns_removed"])]
            + [""]
        )
    if result["changed"]:
        fragment = "{} {} changed".format(
            len(result["changed"]), singular if len(result["changed"]) == 1 else plural
        )
        title.append(fragment)
        if show_headers:
            summary.append(fragment + "\n")
        change_blocks = []
        for details in result["changed"]:
            block = []
            block.append("  {}: {}".format(key, details["key"]))
            for field, (prev_value, current_value) in details["changes"].items():
                block.append(
                    '    {}: "{}" => "{}"'.format(field, prev_value, current_value)
                )
            if extras:
                current_item = current[details["key"]]
                block.append(human_extras(current_item, extras))
            block.append("")
            change_blocks.append("\n".join(block))
            if details.get("unchanged"):
                block = []
                block.append("    Unchanged:")
                for field, value in details["unchanged"].items():
                    block.append('      {}: "{}"'.format(field, value))
                block.append("")
                change_blocks.append("\n".join(block))
        summary.append("\n".join(change_blocks))
    if result["added"]:
        fragment = "{} {} added".format(
            len(result["added"]), singular if len(result["added"]) == 1 else plural
        )
        title.append(fragment)
        if show_headers:
            summary.append(fragment + "\n")
        rows = []
        for row in result["added"]:
            to_append = human_row(row, prefix="  ")
            if extras:
                to_append += "\n" + human_extras(row, extras)
            rows.append(to_append)
        summary.append("\n\n".join(rows))
        summary.append("")
    if result["removed"]:
        fragment = "{} {} removed".format(
            len(result["removed"]), singular if len(result["removed"]) == 1 else plural
        )
        title.append(fragment)
        if show_headers:
            summary.append(fragment + "\n")
        rows = []
        for row in result["removed"]:
            to_append = human_row(row, prefix="  ")
            if extras:
                to_append += "\n" + human_extras(row, extras)
            rows.append(to_append)
        summary.append("\n\n".join(rows))
        summary.append("")
    return (", ".join(title) + "\n\n" + ("\n".join(summary))).strip()


def human_row(row, prefix=""):
    bits = []
    for key, value in row.items():
        bits.append("{}{}: {}".format(prefix, key, value))
    return "\n".join(bits)


def human_extras(row, extras):
    bits = []
    bits.append("  extras:")
    for key, fmt in extras:
        bits.append("    {}: {}".format(key, fmt.format(**row)))
    return "\n".join(bits)
