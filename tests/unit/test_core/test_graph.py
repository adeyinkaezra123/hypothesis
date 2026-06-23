"""Tests for the table dependency graph."""

import pytest

from hypothesis.core.exceptions import CircularDependencyError
from hypothesis.core.graph import DependencyGraph
from hypothesis.core.models import ForeignKey


def _fk(table: str, referenced: str) -> ForeignKey:
    return ForeignKey(
        table=table,
        column=f"{referenced}_id",
        referenced_table=referenced,
        referenced_column="id",
    )


def test_parents_come_before_children() -> None:
    graph = DependencyGraph()
    graph.build_from_foreign_keys(
        [_fk("posts", "users"), _fk("comments", "posts"), _fk("comments", "users")]
    )
    order = graph.topological_sort()
    assert order.index("users") < order.index("posts") < order.index("comments")


def test_isolated_tables_are_included() -> None:
    graph = DependencyGraph(tables=["alpha", "beta"])
    graph.build_from_foreign_keys([])
    assert sorted(graph.topological_sort()) == ["alpha", "beta"]


def test_self_reference_does_not_break_ordering_or_report_a_cycle() -> None:
    graph = DependencyGraph()
    graph.build_from_foreign_keys([_fk("employees", "employees")])
    assert graph.topological_sort() == ["employees"]
    assert graph.detect_cycles() == []


def test_get_layers_groups_by_depth() -> None:
    graph = DependencyGraph()
    graph.build_from_foreign_keys([_fk("posts", "users"), _fk("comments", "posts")])
    assert graph.get_layers() == [["users"], ["posts"], ["comments"]]


def test_detect_cycles_finds_a_two_table_cycle() -> None:
    graph = DependencyGraph()
    graph.build_from_foreign_keys(
        [ForeignKey("a", "b_id", "b", "id"), ForeignKey("b", "a_id", "a", "id")]
    )
    cycles = graph.detect_cycles()
    assert len(cycles) == 1
    assert sorted(cycles[0]) == ["a", "b"]


def test_topological_sort_raises_on_cycle() -> None:
    graph = DependencyGraph()
    graph.build_from_foreign_keys(
        [ForeignKey("a", "b_id", "b", "id"), ForeignKey("b", "a_id", "a", "id")]
    )
    with pytest.raises(CircularDependencyError):
        graph.topological_sort()


def test_acyclic_graph_reports_no_cycles() -> None:
    graph = DependencyGraph()
    graph.build_from_foreign_keys([_fk("posts", "users")])
    assert graph.detect_cycles() == []
