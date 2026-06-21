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


def test_compare_two_empty_inputs_returns_no_differences():
    """Two empty diff inputs should produce a clean "no diff" result
    instead of a raw StopIteration from the next(iter(...)) call on
    previous_columns."""
    diff = compare({}, {})
    assert diff == {
        "added": [],
        "removed": [],
        "changed": [],
        "columns_added": [],
        "columns_removed": [],
    }


def test_compare_previous_empty_reports_all_rows_as_added():
    """If the previous file is empty (header-only), every row in the
    current file should appear under 'added' and the columns should be
    reported as columns_added."""
    current = {"a": {"id": "1", "name": "x"}}
    diff = compare({}, current)
    assert diff["added"] == [{"id": "1", "name": "x"}]
    assert diff["removed"] == []
    assert diff["changed"] == []
    assert set(diff["columns_added"]) == {"id", "name"}
    assert diff["columns_removed"] == []


def test_compare_current_empty_reports_all_rows_as_removed():
    """If the current file is empty (header-only), every row in the
    previous file should appear under 'removed' and the columns should
    be reported as columns_removed."""
    previous = {"a": {"id": "1", "name": "x"}}
    diff = compare(previous, {})
    assert diff["added"] == []
    assert diff["removed"] == [{"id": "1", "name": "x"}]
    assert diff["changed"] == []
    assert diff["columns_added"] == []
    assert set(diff["columns_removed"]) == {"id", "name"}


def test_compare_both_empty_does_not_crash():
    """Sanity check: the original bug was a raw StopIteration reaching
    the user. Guard against it regressing."""
    try:
        compare({}, {})
    except StopIteration:
        raise AssertionError(
            "compare() must not raise StopIteration for empty inputs"
        )
