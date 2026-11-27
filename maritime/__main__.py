"""Print the starter graph and its expected outcome."""

from .toy_graph import EDGES, EXPECTED_DISTANCE_KM, EXPECTED_PATH, GOAL, START


def main() -> None:
    print(f"Toy graph to use when implementing A*: {START} to {GOAL}")
    for cell, edges in EDGES.items():
        destinations = ", ".join(f"{node} ({km:g} km)" for node, km in edges)
        print(f"  {cell}: {destinations or 'isolated'}")
    path = " -> ".join(EXPECTED_PATH)
    print(f"Expected shortest route: {path} ({EXPECTED_DISTANCE_KM:g} km)")


if __name__ == "__main__":
    main()
