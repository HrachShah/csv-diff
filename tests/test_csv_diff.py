from csv_diff import load_csv, load_json, compare
import pytest
import io

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


def test_load_csv_rejects_null_key_values():
    with pytest.raises(ValueError, match="contains a null value"):
        load_csv(io.StringIO("id,name\n,Cleo"), key="id")


def test_load_json_rejects_null_key_values():
    with pytest.raises(ValueError, match="contains a null value"):
        load_json(io.StringIO('[{"id": null, "name": "Cleo"}]'), key="id")


def test_load_json_rejects_empty_key_values():
    with pytest.raises(ValueError, match="contains a null value"):
        load_json(io.StringIO('[{"id": "", "name": "Cleo"}]'), key="id")


def test_load_json_rejects_non_object_items():
    with pytest.raises(ValueError, match="array of objects"):
        load_json(io.StringIO('[{"id": 1}, "not an object"]'))


def test_load_json_rejects_non_array_root():
    with pytest.raises(ValueError, match="array of objects"):
        load_json(io.StringIO('{"id": 1}'))


def test_load_csv_rejects_duplicate_key_values():
    with pytest.raises(ValueError, match="Duplicate key value: '1'"):
        load_csv(io.StringIO("id,name\n1,Cleo\n1,Pancakes"), key="id")


def test_load_json_rejects_duplicate_key_values():
    with pytest.raises(ValueError, match="Duplicate key value: 1"):
        load_json(io.StringIO('[{"id": 1, "name": "Cleo"}, {"id": 1, "name": "Pancakes"}]'), key="id")


def test_load_csv_rejects_rows_with_wrong_field_count():
    with pytest.raises(ValueError, match=r"Row 2 has 1 fields; expected at least 2"):
        load_csv(io.StringIO("id,name\n1"), key="id")


def test_load_csv_rejects_duplicate_header_fields():
    with pytest.raises(ValueError, match="duplicate field names"):
        load_csv(io.StringIO("id,name,name\n1,Cleo,4"), key="id")


def test_load_csv_accepts_empty_input():
    assert load_csv(io.StringIO(""), key="id") == {}


def test_load_csv_rejects_nonempty_extra_fields():
    with pytest.raises(ValueError, match=r"Row 2 has 3 fields; expected at most 2"):
        load_csv(io.StringIO("id,name\n1,Cleo,unexpected"), key="id")
