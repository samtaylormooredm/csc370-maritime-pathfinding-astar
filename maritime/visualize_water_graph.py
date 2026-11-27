"""Build a Folium map of a regional H3 water graph."""

import argparse
from collections import deque
from html import escape
from pathlib import Path

import folium
import geopandas as gpd
import h3
from shapely import STRtree, box
from shapely.geometry import LineString, Polygon

CYCLADES_BOUNDS = (24.70, 36.85, 25.70, 37.48)


def read_land(paths, bounds):
    """Read the regional parts of the land and minor-islands datasets."""
    region = box(*bounds)
    layers = []
    for path in paths:
        layer = gpd.read_file(path, bbox=bounds).to_crs("EPSG:4326")
        clipped = layer.geometry.make_valid().intersection(region)
        layers.extend(geom for geom in clipped if not geom.is_empty)
    return gpd.GeoSeries(layers, crs="EPSG:4326")


def build_water_graph(bounds, resolution, land):
    """Return allowed cell polygons, their H3 centers, and their adjacency."""
    west, south, east, north = bounds
    area = h3.LatLngPoly(
        [(south, west), (south, east), (north, east), (north, west)]
    )
    region = box(*bounds)
    land_index = STRtree(land)
    water = {}
    for cell in sorted(h3.h3shape_to_cells(area, resolution)):
        polygon = Polygon(
            [(lon, lat) for lat, lon in h3.cell_to_boundary(cell)]
        )
        if region.covers(polygon) and not land_index.query(
            polygon, predicate="intersects"
        ).size:
            water[cell] = polygon

    centers = {cell: h3.cell_to_latlng(cell) for cell in water}
    edges = {cell: set() for cell in water}
    for cell in water:
        for neighbor in h3.grid_disk(cell, 1):
            if neighbor <= cell or neighbor not in water:
                continue
            segment = LineString([centers[cell][::-1], centers[neighbor][::-1]])
            if not land_index.query(segment, predicate="intersects").size:
                edges[cell].add(neighbor)
                edges[neighbor].add(cell)
    return water, centers, edges


def reachable_cells(start, edges):
    reached = {start}
    frontier = deque([start])
    while frontier:
        for neighbor in edges[frontier.popleft()] - reached:
            reached.add(neighbor)
            frontier.append(neighbor)
    return reached


def add_cells(map_, name, polygons, color, show=True):
    if not polygons:
        return
    cells = gpd.GeoDataFrame(
        {"cell": list(polygons)}, geometry=list(polygons.values()), crs="EPSG:4326"
    )
    folium.GeoJson(
        cells,
        name=name,
        show=show,
        style_function=lambda _: {"color": color, "weight": 1, "fillOpacity": 0.27},
        tooltip=folium.GeoJsonTooltip(fields=["cell"], aliases=["H3 cell"]),
        smooth_factor=0,
    ).add_to(map_)


def add_ports(map_, ports, water, centers, edges):
    if not ports:
        return
    layer = folium.FeatureGroup(name="Ports and snapped cells").add_to(map_)
    snapped = []
    for name, lat, lon in ports:
        location = (lat, lon)
        cell = min(
            centers,
            key=lambda candidate: h3.great_circle_distance(
                location, centers[candidate], unit="km"
            ),
        )
        center = centers[cell]
        distance_km = h3.great_circle_distance(location, center, unit="km")
        print(f"{name}: {cell} ({distance_km:.2f} km from the input point)")
        folium.Marker(location, tooltip=escape(name)).add_to(layer)
        folium.CircleMarker(
            center,
            radius=5,
            color="#b54708",
            fill=True,
            tooltip=f"{escape(name)} snapped · {distance_km:.2f} km · {cell}",
        ).add_to(layer)
        snapped.append(cell)

    start = snapped[0]
    reached = reachable_cells(start, edges)
    add_cells(
        map_,
        "Cells reachable from first port",
        {cell: polygon for cell, polygon in water.items() if cell in reached},
        "#0e7a5f",
        show=False,
    )
    if len(snapped) == 2:
        print(f"Distinct port cells: {'yes' if start != snapped[1] else 'no'}")
        print(f"Second port reachable: {'yes' if snapped[1] in reached else 'no'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--land", type=Path, default=Path("data/raw/ne_10m_land.zip"))
    parser.add_argument(
        "--minor-islands",
        type=Path,
        default=Path("data/raw/ne_10m_minor_islands.zip"),
    )
    parser.add_argument("--resolution", type=int, choices=range(16), default=7)
    parser.add_argument(
        "--bounds",
        nargs=4,
        type=float,
        default=CYCLADES_BOUNDS,
        metavar=("WEST", "SOUTH", "EAST", "NORTH"),
    )
    parser.add_argument(
        "--port",
        nargs=3,
        action="append",
        default=[],
        metavar=("NAME", "LAT", "LON"),
        help="Supply once or twice to visualize port snapping and connectivity.",
    )
    parser.add_argument("--output", type=Path, default=Path("outputs/water_graph.html"))
    args = parser.parse_args()

    west, south, east, north = args.bounds
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        parser.error("--bounds must be an ordered WEST SOUTH EAST NORTH rectangle")
    if len(args.port) > 2:
        parser.error("supply --port at most twice")
    ports = []
    for name, lat_text, lon_text in args.port:
        try:
            lat, lon = float(lat_text), float(lon_text)
        except ValueError:
            parser.error("--port requires numeric latitude and longitude")
        if not (south <= lat <= north and west <= lon <= east):
            parser.error(f"{name} is outside the study bounds")
        ports.append((name, lat, lon))
    for path in (args.land, args.minor_islands):
        if not path.is_file():
            parser.error(f"data file missing: {path}")

    land = read_land((args.land, args.minor_islands), args.bounds)
    water, centers, edges = build_water_graph(args.bounds, args.resolution, land)
    if not water:
        parser.error("no water cells found in the study region at this resolution")

    map_ = folium.Map(tiles="OpenStreetMap")
    map_.fit_bounds([(south, west), (north, east)])
    if not land.empty:
        folium.GeoJson(
            land,
            name="Mapped land and minor islands",
            style_function=lambda _: {
                "color": "#5b6068",
                "weight": 1,
                "fillOpacity": 0.38,
            },
            smooth_factor=0,
        ).add_to(map_)
    add_cells(map_, "H3 water cells", water, "#2869a5")
    edge_layer = folium.FeatureGroup(name="Allowed neighbor edges", show=False)
    segments = [
        (centers[cell], centers[neighbor])
        for cell, neighbors in edges.items()
        for neighbor in sorted(neighbors)
        if cell < neighbor
    ]
    if segments:
        folium.PolyLine(segments, color="#10395c", weight=1).add_to(edge_layer)
    edge_layer.add_to(map_)
    add_ports(map_, ports, water, centers, edges)
    folium.LayerControl(collapsed=False).add_to(map_)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    map_.save(str(args.output))
    print(f"Saved {args.output} ({len(water):,} water cells, {len(segments):,} edges)")


if __name__ == "__main__":
    main()
