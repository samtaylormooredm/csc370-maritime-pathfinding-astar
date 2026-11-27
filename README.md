# Maritime Pathfinding with A*

CSC 370 final project by Samantha Taylormoore and Rafae Kamran. The goal is to find short port-to-port routes through an H3 water graph in the Cyclades and measure how much direct-distance guidance improves search.

## Run the starter

From the repository root with Python 3.10 or newer:

```bash
python3 -m maritime
```

The command prints a small weighted graph and its known optimal route. The starter uses only the standard library. Implementing the search and connecting it to real map data are the first project tasks.

- [Project plan and work split](PLAN.md)
- [Search interface](maritime/routing.py)
- [Sample graph for local development](maritime/toy_graph.py)
