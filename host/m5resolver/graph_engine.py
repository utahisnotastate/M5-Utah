from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("m5resolver.graph")


class UnitNode:
    def __init__(self, name: str, attributes: dict[str, Any]) -> None:
        self.name = name
        self.attributes = attributes
        self.dependencies: set[str] = set()


class StateGraphEngine:
    """
    DAG-driven dynamic state topologies for minimal registry mutation trees.
    """

    def __init__(self) -> None:
        self.nodes: dict[str, UnitNode] = {}

    def add_reactive_unit(
        self,
        name: str,
        attributes: dict[str, Any],
        depends_on: list[str] | None = None,
    ) -> None:
        node = UnitNode(name, attributes)
        if depends_on:
            for dep in depends_on:
                node.dependencies.add(dep)
        self.nodes[name] = node

    @classmethod
    def from_units(cls, units: dict[str, dict[str, Any]]) -> StateGraphEngine:
        graph = cls()
        for name, attrs in units.items():
            if not isinstance(attrs, dict):
                continue
            deps = attrs.get("depends_on", [])
            dep_list = list(deps) if isinstance(deps, list) else []
            graph.add_reactive_unit(name, attrs, depends_on=dep_list)
        return graph

    def compute_mutation_delta_paths(self, target_changed_node: str) -> list[str]:
        """
        Reverse traversal from a changed root to all downstream dependents.
        Returns top-down cascade initialization order.
        """
        if target_changed_node not in self.nodes:
            return [target_changed_node]

        visited: set[str] = set()
        execution_order: list[str] = []

        def traverse(node_name: str) -> None:
            if node_name in visited:
                return
            visited.add(node_name)
            for name, node in self.nodes.items():
                if node_name in node.dependencies:
                    traverse(name)
            execution_order.append(node_name)

        traverse(target_changed_node)
        return execution_order[::-1]

    def has_cycle(self) -> bool:
        return bool(self.find_cycles())

    def find_cycles(self) -> list[list[str]]:
        cycles: list[list[str]] = []
        visited: set[str] = set()
        stack: set[str] = set()
        path: list[str] = []

        def dfs(node: str) -> None:
            visited.add(node)
            stack.add(node)
            path.append(node)
            node_obj = self.nodes.get(node)
            if node_obj:
                for dep in node_obj.dependencies:
                    if dep not in self.nodes:
                        continue
                    if dep in stack:
                        cycle_start = path.index(dep)
                        cycles.append(path[cycle_start:] + [dep])
                    elif dep not in visited:
                        dfs(dep)
            path.pop()
            stack.remove(node)

        for name in self.nodes:
            if name not in visited:
                dfs(name)
        return cycles

    def validate_dag(self) -> list[str]:
        errors: list[str] = []
        for name, node in self.nodes.items():
            for dep in node.dependencies:
                if dep not in self.nodes:
                    errors.append(f"unit '{name}' depends on unknown node '{dep}'")
        for cycle in self.find_cycles():
            errors.append(f"cyclic dependency detected: {' -> '.join(cycle)}")
        return errors

    def minimal_units_patch(
        self, changed_node: str, all_units: dict[str, dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        paths = self.compute_mutation_delta_paths(changed_node)
        return {unit_id: all_units[unit_id] for unit_id in paths if unit_id in all_units}

    def slot_index_for_unit(self, unit_id: str) -> int | None:
        node = self.nodes.get(unit_id)
        if node is None:
            return None
        slot = node.attributes.get("slot_id")
        if isinstance(slot, int) and 0 <= slot <= 15:
            return slot
        return None

    def build_slot_frequency_map(
        self, unit_ids: list[str], all_units: dict[str, dict[str, Any]]
    ) -> dict[int, int]:
        updates: dict[int, int] = {}
        for idx, unit_id in enumerate(unit_ids):
            slot = self.slot_index_for_unit(unit_id)
            if slot is None:
                slot = idx if idx < 16 else None
            if slot is None:
                continue
            unit = all_units.get(unit_id, {})
            freq = int(unit.get("frequency_hz", 2))
            updates[slot] = freq
        return updates
