import pytest
from csv_diff import load_csv, compare
import io
import json

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


def test_load_empty_csv():
    assert load_csv(io.StringIO(""), key="id") == {}


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


def test_compare_with_empty_previous():
    # If 'previous' contains no rows, the diff should report all current
    # rows as 'added' and the current columns as 'columns_added', instead
    # of crashing on the next(iter(...)) call.
    current = load_csv(io.StringIO(ONE), key="id")
    diff = compare({}, current)
    assert diff == {
        "added": [
            {"id": "1", "name": "Cleo", "age": "4"},
            {"id": "2", "name": "Pancakes", "age": "2"},
        ],
        "removed": [],
        "changed": [],
        "columns_added": sorted(["age", "id", "name"]),
        "columns_removed": [],
    }


def test_compare_with_empty_current():
    # If 'current' contains no rows, the diff should report all previous
    # rows as 'removed' and the previous columns as 'columns_removed'.
    previous = load_csv(io.StringIO(ONE), key="id")
    diff = compare(previous, {})
    assert diff == {
        "added": [],
        "removed": [
            {"id": "1", "name": "Cleo", "age": "4"},
            {"id": "2", "name": "Pancakes", "age": "2"},
        ],
        "changed": [],
        "columns_added": [],
        "columns_removed": sorted(["age", "id", "name"]),
    }


def test_compare_both_empty():
    # Two empty diffs should produce an empty result instead of crashing.
    diff = compare({}, {})
    assert diff == {
        "added": [],
        "removed": [],
        "changed": [],
        "columns_added": [],
        "columns_removed": [],
    }


def test_load_csv_reports_missing_key_column():
    with pytest.raises(KeyError, match="Column 'missing' not found"):
        load_csv(io.StringIO("id,name\n1,Cleo\n"), key="missing")


def test_load_json_rejects_non_list_input():
    with pytest.raises(TypeError, match="JSON input must contain a list"):
        from csv_diff import load_json

        load_json(io.StringIO('{"id": 1}'))


def test_load_json_rejects_non_object_records():
    from csv_diff import load_json

    with pytest.raises(TypeError, match="JSON input records must be objects"):
        load_json(io.StringIO('[{"id": 1}, null]'))


def test_load_csv_rejects_duplicate_keys():
    with pytest.raises(ValueError, match="Duplicate key '1' in CSV input"):
        load_csv(io.StringIO("id,name\n1,Cleo\n1,Clio\n"), key="id")


def test_load_json_rejects_duplicate_keys():
    from csv_diff import load_json

    with pytest.raises(ValueError, match="Duplicate key 1 in JSON input"):
        load_json(io.StringIO('[{"id": 1, "name": "Cleo"}, {"id": 1, "name": "Clio"}]'), key="id")


def test_load_json_does_not_mutate_input_records():
    from csv_diff import load_json

    source = [{"id": 1, "labels": ["one"]}]
    result = load_json(io.StringIO(json.dumps(source)), key="id")

    assert source == [{"id": 1, "labels": ["one"]}]
    assert result[1]["labels"] == '["one"]'


def test_load_csv_rejects_ragged_rows():
    with pytest.raises(ValueError, match="CSV row ending at line 2 has 2 fields; expected 3"):
        load_csv(io.StringIO("id,name,age\n1,Cleo\n"), key="id")


def test_load_csv_rejects_rows_with_extra_fields():
    with pytest.raises(ValueError, match="CSV row ending at line 2 has 4 fields; expected 3"):
        load_csv(io.StringIO("id,name,age\n1,Cleo,4,unexpected\n"), key="id")
