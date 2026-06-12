from csv_diff import load_csv, load_json, compare
import io
import pytest

ONE = """id,name,age
1,Cleo,4
2,Pancakes,2"""

ONE_TSV = """id\tname\tage
1\tCleo\t4
2\tPancakes\t2"""

TWO = """id,name,age
1,Cleo,5
2,Pancakes,2"""

TWO_TSV = """id\tname\tage
1\tCleo\t5
2\tPancakes\t2"""

THREE = """id,name,age
1,Cleo,5"""

FOUR = """id,name,age
1,Cleo,5
2,Pancakes,2,
3,Bailey,1"""

FIVE = """id,name,age
1,Cleo,5
2,Pancakes,2,
3,Bailey,1
4,Carl,7"""

SIX = """id,name,age
1,Cleo,5
3,Bailey,1"""

SEVEN = """id,name,weight
1,Cleo,48
3,Bailey,20"""

EIGHT = """id,name,age,length
3,Bailee,1,100
4,Bob,7,422"""

NINE = """id,name,age
1,Cleo,5
2,Pancakes,4"""

TEN = """id,name,age
1,Cleo,5
2,Pancakes,3"""


def test_row_changed():
    diff = compare(
        load_csv(io.StringIO(ONE), key="id"), load_csv(io.StringIO(TWO), key="id")
    )
    assert {
        "added": [],
        "removed": [],
        "changed": [{"key": "1", "changes": {"age": ["4", "5"]}}],
        "columns_added": [],
        "columns_removed": [],
    } == diff


def test_row_added():
    diff = compare(
        load_csv(io.StringIO(THREE), key="id"), load_csv(io.StringIO(TWO), key="id")
    )
    assert {
        "changed": [],
        "removed": [],
        "added": [{"age": "2", "id": "2", "name": "Pancakes"}],
        "columns_added": [],
        "columns_removed": [],
    } == diff


def test_row_removed():
    diff = compare(
        load_csv(io.StringIO(TWO), key="id"), load_csv(io.StringIO(THREE), key="id")
    )
    assert {
        "changed": [],
        "removed": [{"age": "2", "id": "2", "name": "Pancakes"}],
        "added": [],
        "columns_added": [],
        "columns_removed": [],
    } == diff


def test_columns_changed():
    diff = compare(
        load_csv(io.StringIO(SIX), key="id"), load_csv(io.StringIO(SEVEN), key="id")
    )
    assert {
        "changed": [],
        "removed": [],
        "added": [],
        "columns_added": ["weight"],
        "columns_removed": ["age"],
    } == diff


def test_tsv():
    diff = compare(
        load_csv(io.StringIO(ONE), key="id"), load_csv(io.StringIO(TWO_TSV), key="id")
    )
    assert {
        "added": [],
        "removed": [],
        "changed": [{"key": "1", "changes": {"age": ["4", "5"]}}],
        "columns_added": [],
        "columns_removed": [],
    } == diff


def test_load_csv_empty_file_returns_empty_dict():
    # A truly empty CSV has no header line for `next(fp)` to read, so
    # `next(fp)` used to raise StopIteration. Returning {} keeps the CLI's
    # `csv-diff empty.csv empty.csv` path alive and lets compare() short-circuit.
    assert load_csv(io.StringIO("")) == {}


def test_load_csv_header_only_returns_empty_dict():
    # Header-only files have a header row but no data rows, so load_csv should
    # return an empty dict (the header still parses, rows list is empty).
    assert load_csv(io.StringIO("id,name,age\n")) == {}


def test_load_csv_missing_key_column_raises_descriptive_keyerror():
    # The previous code did `r[key]` and let a bare KeyError bubble up. The new
    # message names the missing column and the available headers so the user
    # can fix the --key argument without reading source code.
    with pytest.raises(KeyError, match=r"Column 'bogus' not found in CSV header"):
        load_csv(io.StringIO("id,name\n1,Cleo\n"), key="bogus")


def test_load_json_empty_list_returns_empty_dict():
    # An empty JSON list has no records to key on; return {} so it composes
    # with compare() and the CLI the same way an empty CSV does.
    assert load_json(io.StringIO("[]")) == {}


def test_load_json_missing_key_column_raises_descriptive_keyerror():
    with pytest.raises(KeyError, match=r"Column 'bogus' not found in JSON record"):
        load_json(io.StringIO('[{"id":1,"name":"Cleo"}]'), key="bogus")


def test_compare_with_empty_previous_marks_all_current_as_added():
    # next(iter(previous.values())) used to raise StopIteration when previous
    # was empty, crashing the whole diff. The new short-circuit marks every
    # row in current as added (no per-row comparison is possible without a
    # reference row's columns).
    diff = compare({}, {"a": {"id": "1", "name": "Cleo"}})
    assert diff["added"] == [{"id": "1", "name": "Cleo"}]
    assert diff["removed"] == []
    assert diff["changed"] == []


def test_compare_with_empty_current_marks_all_previous_as_removed():
    diff = compare({"a": {"id": "1", "name": "Cleo"}}, {})
    assert diff["removed"] == [{"id": "1", "name": "Cleo"}]
    assert diff["added"] == []
    assert diff["changed"] == []


def test_compare_with_both_empty_returns_empty_diff():
    # The previous code's `next(iter(previous.values()))` raised StopIteration
    # on two empty dicts. The new short-circuit returns a clean empty diff.
    assert compare({}, {}) == {
        "added": [],
        "removed": [],
        "changed": [],
        "columns_added": [],
        "columns_removed": [],
    }
