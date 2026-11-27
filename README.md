# Maritime Pathfinding with A*

CSC 370 final project by Samantha Taylormoore and Rafae Kamran. This project explores port-to-port pathfinding in the Aegean Sea using an H3 water graph. The goal is to find short routes that avoid mapped land and compare how many cells A* and uniform-cost search expand.

## Setup

From the repository root, create a virtual environment and install the dependencies. Use Python 3.12.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Download the Natural Earth land and minor-island layers. Keep both files as ZIPs.

```bash
mkdir -p data/raw

curl -fL https://naturalearth.s3.amazonaws.com/10m_physical/ne_10m_land.zip \
  -o data/raw/ne_10m_land.zip

curl -fL https://naturalearth.s3.amazonaws.com/10m_physical/ne_10m_minor_islands.zip \
  -o data/raw/ne_10m_minor_islands.zip
```

## Run the seeded map

```bash
python -m maritime.seeded_map
```

Open [the map on localhost](http://127.0.0.1:8002/). Enter an integer seed and click **Generate** to select two islands, place a synthetic port on each coastline, and show the H3 water cells inside a padded rectangle around both islands. The same seed reproduces the same pair with the same data. Use the **Candidate islands** layer to see the full selection area.

The map starts at seed `42` and H3 resolution `6`. To try a finer grid, start the server with `--resolution 7`.