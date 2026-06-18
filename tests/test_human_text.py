from csv_diff import load_csv, compare, human_text
from .test_csv_diff import ONE, TWO, THREE, FOUR, FIVE, SIX, SEVEN, EIGHT, NINE, TEN
from textwrap import dedent
import io


def test_row_changed():
    diff = compare(
        load_csv(io.StringIO(ONE), key="id"), load_csv(io.StringIO(TWO), key="id")
    )
    assert (
        dedent(
            """
    1 row changed

      id: 1
        age: "4" => "5"
    """
        ).strip()
        == human_text(diff, "id")
    )


def test_row_changed_show_unchanged():
    diff = compare(
        load_csv(io.StringIO(ONE), key="id"),
        load_csv(io.StringIO(TWO), key="id"),
        show_unchanged=True,
    )
    assert (
        dedent(
            """
    1 row changed

      id: 1
        age: "4" => "5"

        Unchanged:
          name: "Cleo"
    """
        ).strip()
        == human_text(diff, "id")
    )


def test_row_added():
    diff = compare(
        load_csv(io.StringIO(THREE), key="id"), load_csv(io.StringIO(TWO), key="id")
    )
    assert (
        dedent(
            """
    1 row added

      id: 2
      name: Pancakes
      age: 2
    """
        ).strip()
        == human_text(diff, "id")
    )


def test_rows_added():
    diff = compare(
        load_csv(io.StringIO(THREE), key="id"), load_csv(io.StringIO(FIVE), key="id")
    )
    assert (
        dedent(
            """
    3 rows added

      id: 2
      name: Pancakes
      age: 2

      id: 3
      name: Bailey
      age: 1

      id: 4
      name: Carl
      age: 7
    """
        ).strip()
        == human_text(diff, "id")
    )


def test_row_removed():
    diff = compare(
        load_csv(io.StringIO(TWO), key="id"), load_csv(io.StringIO(THREE), key="id")
    )
    assert (
        dedent(
            """
    1 row removed

      id: 2
      name: Pancakes
      age: 2
    """
        ).strip()
        == human_text(diff, "id")
    )


def test_row_changed_and_row_added_and_row_deleted():
    "Should have headers for each section here"
    diff = compare(
        load_csv(io.StringIO(ONE), key="id"), load_csv(io.StringIO(SIX), key="id")
    )
    assert (
        dedent(
            """
    1 row changed, 1 row added, 1 row removed

    1 row changed

      id: 1
        age: "4" => "5"

    1 row added

      id: 3
      name: Bailey
      age: 1

    1 row removed

      id: 2
      name: Pancakes
      age: 2
    """
        ).strip()
        == human_text(diff, "id")
    )


def test_columns_changed():
    diff = compare(
        load_csv(io.StringIO(SIX), key="id"), load_csv(io.StringIO(SEVEN), key="id")
    )
    assert (
        dedent(
            """
    1 column added, 1 column removed

    1 column added

      weight

    1 column removed

      age
    """
        ).strip()
        == human_text(diff, "id")
    )


def test_columns_and_rows_changed():
    diff = compare(
        load_csv(io.StringIO(SEVEN), key="id"), load_csv(io.StringIO(EIGHT), key="id")
    )
    assert (
        dedent(
            """
    2 columns added, 1 column removed, 1 row changed, 1 row added, 1 row removed

    2 columns added

      age
      length

    1 column removed

      weight

    1 row changed

      id: 3
        name: "Bailey" => "Bailee"

    1 row added

      id: 4
      name: Bob
      age: 7
      length: 422

    1 row removed

      id: 1
      name: Cleo
      weight: 48
    """
        ).strip()
        == human_text(diff, "id")
    )


def test_no_key():
    diff = compare(load_csv(io.StringIO(NINE)), load_csv(io.StringIO(TEN)))
    assert (
        dedent(
            """
        1 row added, 1 row removed

        1 row added

          id: 2
          name: Pancakes
          age: 3

        1 row removed

          id: 2
          name: Pancakes
          age: 4
        """
        ).strip()
        == human_text(diff)
    )


def test_no_key_changed_row_does_not_render_none_prefix():
    """human_text used to render the changed-row identifier line as
    '  None: <hash>' when the caller didn't pass a key column name and
    the diff had 'changed' rows. The function parameter 'key' defaults
    to None, and the format() call '{key}: {details[\"key\"]}' plugged
    None through verbatim. In no-key mode there is no column name to
    display, so the row identifier is just the content hash on its own
    line. Pin that the literal 'None' is never rendered and that the
    row hash is the only identifier on the first line of the block."""
    ONE = "id,name,age\n1,Cleo,4\n2,Pancakes,2"
    TWO = "id,name,age\n1,Cleo,5\n2,Pancakes,2"
    diff = compare(
        load_csv(io.StringIO(ONE), key="id"),
        load_csv(io.StringIO(TWO), key="id"),
    )
    # Build a no-key diff by re-hashing on content instead of the id column.
    no_key_diff = compare(
        load_csv(io.StringIO(ONE)),
        load_csv(io.StringIO(TWO)),
    )
    # No-key content hashes collide when rows differ, so the diff classifies
    # the change as added/removed rather than 'changed'. To exercise the
    # no-key + changed code path directly, monkey-build a 'changed' diff
    # and call human_text with no key.
    no_key_changed = {
        "added": [],
        "removed": [],
        "changed": [{"key": "abc123", "changes": {"age": ["4", "5"]}}],
        "columns_added": [],
        "columns_removed": [],
    }
    out = human_text(no_key_changed)
    assert "None" not in out, f"unexpected 'None' in human_text output: {out!r}"
    assert "abc123" in out
    assert out.startswith("1 row changed\n\n  abc123")
