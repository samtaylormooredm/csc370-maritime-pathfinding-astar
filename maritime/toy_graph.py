"""An offline fixture with a cheaper two-edge path and an isolated cell."""

from .routing import Cell

EDGES: dict[Cell, tuple[tuple[Cell, float], ...]] = {
    "A": (("B", 4.0), ("D", 10.0)),
    "B": (("A", 4.0), ("D", 4.0)),
    "D": (("A", 10.0), ("B", 4.0)),
    "E": (),
}
START: Cell = "A"
GOAL: Cell = "D"
EXPECTED_PATH: tuple[Cell, ...] = ("A", "B", "D")
EXPECTED_DISTANCE_KM = 8.0


def neighbors(cell: Cell) -> tuple[tuple[Cell, float], ...]:
    return EDGES[cell]
