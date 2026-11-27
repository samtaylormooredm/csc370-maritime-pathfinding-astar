"""Shared interface for the search algorithm and water graph."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass

Cell = str
Neighbors = Callable[[Cell], Iterable[tuple[Cell, float]]]
Heuristic = Callable[[Cell, Cell], float]


@dataclass(frozen=True)
class SearchResult:
    """Search outcome, including expansions even when no route exists."""

    path: tuple[Cell, ...] | None
    distance_km: float | None
    expanded: int


def astar(
    start: Cell,
    goal: Cell,
    neighbors: Neighbors,
    heuristic: Heuristic,
) -> SearchResult:
    """Find the least-cost path using nonnegative edge distances in kilometers.

    Count a cell as expanded when search examines its outgoing neighbors.
    Return None for both path and distance if the frontier is exhausted.
    A zero heuristic runs uniform-cost search on the same graph.
    """
    raise NotImplementedError("Implement A* against the toy graph first.")
