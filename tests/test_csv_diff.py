from csv_diff import load_csv, compare
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


def test_load_csv_empty_file():
    diff = load_csv(io.StringIO(""))
    assert diff == {}


def test_compare_empty_previous():
    diff = compare({}, {"1": {"id": "1", "name": "Cleo", "age": "5"}}, show_unchanged=True)
    assert diff["added"] == [{"id": "1", "name": "Cleo", "age": "5"}]
    assert diff["removed"] == []
    assert diff["changed"] == []
    assert sorted(diff["columns_added"]) == ["age", "id", "name"]
    assert diff["columns_removed"] == []


def test_compare_empty_current():
    diff = compare({"1": {"id": "1", "name": "Cleo", "age": "5"}}, {})
    assert diff["added"] == []
    assert diff["removed"] == [{"id": "1", "name": "Cleo", "age": "5"}]
    assert diff["changed"] == []
    assert diff["columns_added"] == []
    assert sorted(diff["columns_removed"]) == ["age", "id", "name"]


def test_compare_both_empty():
    diff = compare({}, {})
    assert diff == {
        "added": [],
        "removed": [],
        "changed": [],
        "columns_added": [],
        "columns_removed": [],
    }