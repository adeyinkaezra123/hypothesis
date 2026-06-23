"""Table dependency graph for foreign-key-aware insertion ordering."""

from __future__ import annotations

from hypothesis.core.exceptions import CircularDependencyError
from hypothesis.core.models import ForeignKey


class DependencyGraph:
    """Directed graph of table dependencies derived from foreign keys.

    ``b in edges[a]`` means table ``a`` depends on table ``b`` — ``b`` must be
    inserted before ``a``. Self-referential foreign keys are ignored for
    ordering (they are handled separately via a two-pass insert strategy).
    """

    def __init__(self, tables: list[str] | None = None) -> None:
        self.tables: list[str] = []
        self.edges: dict[str, set[str]] = {}
        for table in tables or []:
            self.add_table(table)

    def add_table(self, name: str) -> None:
        """Register a table. Idempotent."""
        if name not in self.edges:
            self.edges[name] = set()
            self.tables.append(name)

    def build_from_foreign_keys(self, foreign_keys: list[ForeignKey]) -> None:
        """Add an edge for each foreign key (skipping self-references)."""
        for fk in foreign_keys:
            self.add_table(fk.table)
            self.add_table(fk.referenced_table)
            if fk.table != fk.referenced_table:
                self.edges[fk.table].add(fk.referenced_table)

    def topological_sort(self) -> list[str]:
        """Return tables ordered so dependencies precede dependents.

        Raises:
            CircularDependencyError: if the graph contains a cycle.
        """
        order: list[str] = []
        for layer in self.get_layers():
            order.extend(layer)
        return order

    def get_layers(self) -> list[list[str]]:
        """Group tables into dependency layers.

        Layer 0 has no dependencies; layer ``k`` depends only on earlier layers.
        Tables within a layer can be inserted independently. Within each layer
        tables are sorted for deterministic output.

        Raises:
            CircularDependencyError: if the graph contains a cycle.
        """
        remaining = {table: set(deps) for table, deps in self.edges.items()}
        layers: list[list[str]] = []
        while remaining:
            ready = sorted(table for table, deps in remaining.items() if not deps)
            if not ready:
                stuck = ", ".join(sorted(remaining))
                raise CircularDependencyError(
                    f"Circular foreign key dependency among tables: {stuck}"
                )
            layers.append(ready)
            for table in ready:
                del remaining[table]
            for deps in remaining.values():
                deps.difference_update(ready)
        return layers

    def detect_cycles(self) -> list[list[str]]:
        """Return groups of tables that form circular dependencies.

        Each group is a strongly connected component of size greater than one.
        Self-references are excluded from the graph, so they never appear here.
        Returns an empty list when the graph is acyclic.
        """
        return [scc for scc in self._strongly_connected_components() if len(scc) > 1]

    def _strongly_connected_components(self) -> list[list[str]]:
        """Tarjan's strongly connected components.

        Schemas are small (tens of tables), so the recursive form is safe and
        the clearest to read.
        """
        counter = 0
        indices: dict[str, int] = {}
        lowlink: dict[str, int] = {}
        on_stack: set[str] = set()
        stack: list[str] = []
        result: list[list[str]] = []

        def strongconnect(node: str) -> None:
            nonlocal counter
            indices[node] = counter
            lowlink[node] = counter
            counter += 1
            stack.append(node)
            on_stack.add(node)
            for succ in sorted(self.edges.get(node, set())):
                if succ not in indices:
                    strongconnect(succ)
                    lowlink[node] = min(lowlink[node], lowlink[succ])
                elif succ in on_stack:
                    lowlink[node] = min(lowlink[node], indices[succ])
            if lowlink[node] == indices[node]:
                component: list[str] = []
                while True:
                    popped = stack.pop()
                    on_stack.discard(popped)
                    component.append(popped)
                    if popped == node:
                        break
                result.append(sorted(component))

        for node in self.tables:
            if node not in indices:
                strongconnect(node)
        return result
