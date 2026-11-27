"""Serve a seeded H3 water graph for two Aegean islands."""

import argparse
from functools import lru_cache
from pathlib import Path
from random import Random

import folium
import geopandas as gpd
from flask import Flask, render_template_string, request
from shapely import box, buffer, get_parts, union_all
from shapely.ops import nearest_points

from .visualize_water_graph import (
    add_cells,
    add_ports,
    build_water_graph,
    read_land,
)

# Geographic bounds are west, south, east, north.
AEGEAN_BOUNDS = (22.0, 34.5, 29.0, 39.7)
PADDING_DEGREES = 0.25
LAND_PATHS = (
    Path("data/raw/ne_10m_land.zip"),
    Path("data/raw/ne_10m_minor_islands.zip"),
)

PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Aegean water graph</title>
  <style>
    body { margin: 0; font: 16px system-ui, sans-serif; }
    header { padding: 1rem; background: #edf4f8; }
    h1 { margin: 0 0 .6rem; font-size: 1.25rem; }
    input, button { padding: .4rem; font: inherit; }
    p { margin: .6rem 0 0; }
    iframe { display: block; width: 100%; height: 82vh; border: 0; }
  </style>
</head>
<body>
  <header>
    <h1>Aegean water graph</h1>
    <form method="get">
      <label for="seed">Seed</label>
      <input id="seed" name="seed" type="number" step="1"
             value="{{ seed }}" required>
      <button type="submit">Generate</button>
    </form>
    <p>{{ summary }}</p>
  </header>
  {% if map_html %}
    <iframe title="H3 grid around the two selected islands"
            srcdoc="{{ map_html }}"></iframe>
  {% endif %}
</body>
</html>
"""


@lru_cache(maxsize=1)
def load_islands():
    """Load complete island polygons before clipping land to a grid box."""
    region = box(*AEGEAN_BOUNDS)
    land_parts = []
    for path in LAND_PATHS:
        layer = gpd.read_file(path, bbox=AEGEAN_BOUNDS).to_crs("EPSG:4326")
        land_parts.extend(buffer(layer.geometry.to_numpy(), 0))

    # Merge any overlap between the two datasets before counting islands.
    islands = [
        part
        for part in get_parts(union_all(land_parts))
        if part.geom_type == "Polygon" and region.covers(part)
    ]
    # Stable ordering makes the same seed reproducible with the same data.
    return tuple(sorted(islands, key=lambda island: (*island.bounds, island.wkb)))


def select_pair(islands, seed):
    if len(islands) < 2:
        raise ValueError("The study area needs at least two mapped islands.")

    first_id, second_id = Random(seed).sample(range(len(islands)), k=2)
    first, second = islands[first_id], islands[second_id]
    west1, south1, east1, north1 = first.bounds
    west2, south2, east2, north2 = second.bounds
    bounds = (
        min(west1, west2) - PADDING_DEGREES,
        min(south1, south2) - PADDING_DEGREES,
        max(east1, east2) + PADDING_DEGREES,
        max(north1, north2) + PADDING_DEGREES,
    )

    # Place the synthetic ports on the two shorelines facing each other.
    first_port, second_port = nearest_points(first.exterior, second.exterior)
    ports = (
        (f"Island {first_id + 1} · Start", first_port.y, first_port.x),
        (f"Island {second_id + 1} · Goal", second_port.y, second_port.x),
    )
    return bounds, ports


def make_map(seed, resolution):
    islands = load_islands()
    bounds, ports = select_pair(islands, seed)
    west, south, east, north = bounds
    corners = [(south, west), (north, east)]

    land = read_land(LAND_PATHS, bounds)
    water, centers, edges = build_water_graph(bounds, resolution, land)

    map_ = folium.Map(tiles="OpenStreetMap", prefer_canvas=True)
    map_.fit_bounds(corners)

    catalog = gpd.GeoDataFrame(
        {"island": [f"Island {i + 1}" for i in range(len(islands))]},
        geometry=[island.simplify(0.002) for island in islands],
        crs="EPSG:4326",
    )
    folium.GeoJson(
        catalog,
        name="Candidate islands",
        show=False,
        tooltip=folium.GeoJsonTooltip(fields=["island"]),
        style_function=lambda _: {
            "color": "#735e43", "weight": 1, "fillOpacity": 0.15
        },
    ).add_to(map_)

    if not land.empty:
        folium.GeoJson(
            land,
            name="Mapped land inside the box",
            style_function=lambda _: {
                "color": "#555b62", "weight": 1, "fillOpacity": 0.35
            },
        ).add_to(map_)

    add_cells(map_, "H3 water cells", water, "#2869a5")
    folium.Rectangle(corners, color="#163e61", weight=2, fill=False).add_to(map_)

    if centers:
        add_ports(map_, ports, water, centers, edges)
    else:
        for name, lat, lon in ports:
            folium.Marker((lat, lon), tooltip=name).add_to(map_)

    folium.LayerControl(collapsed=False).add_to(map_)
    summary = (
        f"{ports[0][0]} → {ports[1][0]} · "
        f"{len(islands):,} candidates · H3 resolution {resolution} · "
        f"{len(water):,} water cells"
    )
    return map_, summary


def create_app(default_seed, resolution):
    app = Flask(__name__)

    @app.get("/")
    def index():
        try:
            seed = int(request.args.get("seed", default_seed))
        except ValueError:
            return render_template_string(
                PAGE, seed=default_seed, summary="Enter an integer seed."
            ), 400

        map_, summary = make_map(seed, resolution)
        return render_template_string(
            PAGE, seed=seed, summary=summary, map_html=map_.get_root().render()
        )

    return app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--resolution", type=int, choices=range(8), default=6)
    parser.add_argument("--port", type=int, default=8002)
    parser.add_argument("--output", type=Path, help="Save one map as HTML.")
    args = parser.parse_args()

    for path in LAND_PATHS:
        if not path.is_file():
            parser.error(f"Missing land data: {path}")

    if args.output:
        map_, summary = make_map(args.seed, args.resolution)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        map_.save(str(args.output))
        print(summary)
        print(f"Saved {args.output}")
    else:
        create_app(args.seed, args.resolution).run(
            host="127.0.0.1", port=args.port
        )


if __name__ == "__main__":
    main()