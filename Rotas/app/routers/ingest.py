from pathlib import Path
import json
import re
import unicodedata
from math import atan2, cos, radians, sin, sqrt

import pandas as pd
import geopandas as gpd


def normalize_text(txt: str) -> str:
    """Normalize text for safe comparison.

    This helper removes accents, converts to uppercase, and trims whitespace.
    It is used to standardize municipality and zone names during spatial joins.

    Args:
        txt: The input text string.

    Returns:
        A normalized uppercase string without accents, or an empty string if input is not text.
    """
    if not isinstance(txt, str):
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFKD", txt)
        if unicodedata.category(c) != "Mn"
    ).upper().strip()


def _parse_pns_dictionary(dicionario_path: Path, variaveis_alvo):
    """Parse the PNS layout dictionary and extract column specifications.

    The PNS survey provides a fixed-width file layout in a separate dictionary file.
    This function scans that dictionary for the requested variable names and builds
    the `colspecs` tuple list used by pandas.read_fwf.

    Args:
        dicionario_path: Path to the fixed-width dictionary file (input_PNS_2019.txt).
        variaveis_alvo: List of variable names to extract from the dictionary.

    Returns:
        A tuple of (colspecs, nomes_colunas) suitable for pandas.read_fwf.
    """
    colspecs = []
    nomes_colunas = []

    with open(dicionario_path, "r", encoding="latin1") as f:
        for linha in f:
            match = re.search(r"@(?P<start>\d+)\s+(?P<name>[A-Za-z0-9_]+)\s+\$?(?P<width>\d+)\.", linha)
            if match and match.group("name") in variaveis_alvo:
                inicio_py = int(match.group("start")) - 1
                tamanho = int(match.group("width"))
                colspecs.append((inicio_py, inicio_py + tamanho))
                nomes_colunas.append(match.group("name"))

    return colspecs, nomes_colunas


def load_pns_data(dicionario_path: Path, data_path: Path, variaveis_alvo):
    """Load PNS microdata using a dictionary-driven fixed-width schema.

    This function reads the metadata dictionary to select only the relevant columns
    from the PNS fixed-width text file, returning a cleaned pandas DataFrame.

    Args:
        dicionario_path: Path to the dictionary file (`input_PNS_2019.txt`).
        data_path: Path to the fixed-width data file (`PNS_2019.txt`).
        variaveis_alvo: List of PNS variable codes to import.

    Returns:
        A pandas DataFrame containing only the requested PNS variables.
    """
    dicionario_path = Path(dicionario_path)
    data_path = Path(data_path)

    colspecs, nomes_colunas = _parse_pns_dictionary(dicionario_path, variaveis_alvo)
    df = pd.read_fwf(data_path, colspecs=colspecs, names=nomes_colunas, dtype=str)
    df = df.apply(lambda x: x.strip() if isinstance(x, str) else x)
    return df


def load_od_data(sav_path: Path, apply_value_formats: bool = False):
    """Load Origin-Destination microdata from an SPSS .sav file.

    Args:
        sav_path: Path to the OD dataset file (`OD_2017_v1.sav`).
        apply_value_formats: Whether to apply SPSS value labels during import.

    Returns:
        A pandas DataFrame with the raw OD microdata.
    """
    import pyreadstat

    sav_path = Path(sav_path)
    df, meta = pyreadstat.read_sav(sav_path, apply_value_formats=apply_value_formats)
    return df


def load_shape_zones(shapefile_path: Path):
    """Load the spatial zones shapefile used for geographic mapping.

    Reads the `Zonas_2017_region.shp` shapefile and converts the `NumeroZona`
    field to integer so it can be joined against OD zone codes.

    Args:
        shapefile_path: Path to the zones shapefile.

    Returns:
        A GeoDataFrame with zone geometries and normalized zone identifiers.
    """
    shapefile_path = Path(shapefile_path)
    gdf = gpd.read_file(shapefile_path)
    if "NumeroZona" in gdf.columns:
        gdf["NumeroZona"] = pd.to_numeric(gdf["NumeroZona"], errors="coerce").fillna(0).astype(int)
    return gdf


def load_ubs_geojson(geojson_path: Path, target_crs: int = 31983):
    """Load UBS points from GeoJSON and normalize coordinates for analysis.

    This function reads the geoportal UBS dataset and ensures the result uses
    a projected CRS in meters (EPSG:31983) for buffer and spatial join operations.

    Args:
        geojson_path: Path to the UBS GeoJSON file.
        target_crs: EPSG code to convert the data to (default 31983).

    Returns:
        A GeoDataFrame of UBS locations with a consistent projected CRS.
    """
    geojson_path = Path(geojson_path)
    gdf = gpd.read_file(geojson_path)
    if gdf.crs and gdf.crs.to_epsg() == 4326:
        gdf = gdf.to_crs(epsg=target_crs)
    elif gdf.crs is None:
        gdf = gdf.set_crs(epsg=target_crs, allow_override=True)
    return gdf


def load_ubs_points(geojson_path: Path):
    """Load UBS points from GeoJSON into a searchable table.

    This helper reads the raw UBS GeoJSON dataset and extracts latitude,
    longitude, and common address fields into a pandas DataFrame. It also
    builds a normalized `search_text` column that makes text-based location
    matching more reliable for user-provided neighborhood or equipment names.

    Args:
        geojson_path: Path to the UBS GeoJSON file.

    Returns:
        A pandas DataFrame containing UBS metadata with latitude, longitude,
        and a normalized search index.
    """
    geojson_path = Path(geojson_path)
    with geojson_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    records = []
    for feature in data.get("features", []):
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        coords = geometry.get("coordinates") if geometry else None
        if not coords or len(coords) < 2:
            continue

        try:
            lon = float(coords[0])
            lat = float(coords[1])
        except (TypeError, ValueError):
            continue

        records.append({
            "cd_equipamento": properties.get("cd_equipamento"),
            "nm_equipamento": properties.get("nm_equipamento"),
            "tx_endereco_equipamento": properties.get("tx_endereco_equipamento"),
            "nm_bairro_equipamento": properties.get("nm_bairro_equipamento"),
            "nm_tipo_equipamento": properties.get("nm_tipo_equipamento"),
            "latitude": lat,
            "longitude": lon,
        })

    ubs_df = pd.DataFrame(records)
    if ubs_df.empty:
        return ubs_df

    ubs_df["search_text"] = (
        ubs_df[
            [
                "nm_equipamento",
                "tx_endereco_equipamento",
                "nm_bairro_equipamento",
                "nm_tipo_equipamento",
            ]
        ]
        .fillna("")
        .agg(" ".join, axis=1)
        .apply(normalize_text)
    )
    return ubs_df


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points in kilometers.

    Uses the haversine formula on latitude and longitude coordinates to compute
    an approximate earth-surface distance.

    Args:
        lat1: Start latitude in decimal degrees.
        lon1: Start longitude in decimal degrees.
        lat2: End latitude in decimal degrees.
        lon2: End longitude in decimal degrees.

    Returns:
        Distance in kilometers.
    """
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    earth_radius_km = 6371.0
    return earth_radius_km * c


def parse_location_string(location: str, ubs_df: pd.DataFrame):
    """Resolve a free-text location into latitude and longitude.

    This function supports coordinate input in the form "lat,lon" and
    natural-language searches against UBS names, addresses, and neighborhoods.

    Args:
        location: User-provided location text.
        ubs_df: DataFrame containing UBS points and normalized search text.

    Returns:
        A dictionary with resolved latitude/longitude and matching metadata,
        or None if the text could not be resolved.
    """
    if not isinstance(location, str) or not location.strip():
        return None

    text = location.strip()
    coordinate_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", text)
    if coordinate_match:
        return {
            "location_query": text,
            "latitude": float(coordinate_match.group(1)),
            "longitude": float(coordinate_match.group(2)),
            "matched_by": "coordinates",
        }

    normalized_query = normalize_text(text)
    if not normalized_query:
        return None

    exact_matches = ubs_df[ubs_df["search_text"].str.contains(normalized_query, na=False, regex=False)]
    if not exact_matches.empty:
        row = exact_matches.iloc[0]
        return {
            "location_query": text,
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
            "matched_by": "ubs_search",
            "matched_text": row["search_text"],
        }

    tokens = [token for token in re.split(r"[\s,;/-]+", normalized_query) if token]
    if tokens:
        partial_matches = ubs_df[ubs_df["search_text"].apply(lambda value: all(token in value for token in tokens))]
        if not partial_matches.empty:
            row = partial_matches.iloc[0]
            return {
                "location_query": text,
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "matched_by": "ubs_search_tokens",
                "matched_text": row["search_text"],
            }

    return None


def find_nearest_ubs(latitude: float, longitude: float, ubs_df: pd.DataFrame, limit: int = 5):
    """Find the closest UBS points to a given latitude/longitude.

    Args:
        latitude: Origin latitude in decimal degrees.
        longitude: Origin longitude in decimal degrees.
        ubs_df: DataFrame containing UBS point metadata.
        limit: Maximum number of nearest results to return.

    Returns:
        A DataFrame containing the closest UBS points sorted by distance.
    """
    candidates = ubs_df.copy()
    candidates["distance_km"] = candidates.apply(
        lambda row: haversine_distance(latitude, longitude, float(row["latitude"]), float(row["longitude"])),
        axis=1,
    )
    return candidates.sort_values("distance_km").head(limit)


def find_ubs_along_route(current: dict, work: dict, ubs_df: pd.DataFrame, limit: int = 5):
    """Recommend UBS points along the approximate path between current and work locations.

    This function uses a simple route score based on the sum of distances from each UBS
    point to the current and work locations. It does not perform network routing, but
    it helps identify UBS that are reasonably close to the implied travel corridor.

    Args:
        current: Resolved current location with latitude and longitude.
        work: Resolved work location with latitude and longitude.
        ubs_df: DataFrame containing UBS point metadata.
        limit: Maximum number of UPS recommendations.

    Returns:
        A DataFrame of UBS candidates sorted by route score.
    """
    candidates = ubs_df.copy()
    candidates["distance_to_current_km"] = candidates.apply(
        lambda row: haversine_distance(current["latitude"], current["longitude"], float(row["latitude"]), float(row["longitude"])),
        axis=1,
    )
    candidates["distance_to_work_km"] = candidates.apply(
        lambda row: haversine_distance(work["latitude"], work["longitude"], float(row["latitude"]), float(row["longitude"])),
        axis=1,
    )
    candidates["route_score"] = candidates["distance_to_current_km"] + candidates["distance_to_work_km"]
    return candidates.sort_values("route_score").head(limit)


def load_gtfs_data(stops_path: Path, trips_path: Path, stop_times_path: Path, frequencies_path: Path):
    """Load the main GTFS tables required for terminal wait analysis.

    Reads stops, trips, stop times, and frequency information from the GTFS feed.
    Only the columns required for the later computation are imported.

    Args:
        stops_path: Path to `stops.txt`.
        trips_path: Path to `trips.txt`.
        stop_times_path: Path to `stop_times.txt`.
        frequencies_path: Path to `frequencies.txt`.

    Returns:
        A dict with DataFrames for stops, trips, stop_times, and frequencies.
    """
    stops = pd.read_csv(stops_path)
    trips = pd.read_csv(trips_path, usecols=["route_id", "trip_id"])
    stop_times = pd.read_csv(stop_times_path, usecols=["trip_id", "stop_id"])
    frequencies = pd.read_csv(frequencies_path, usecols=["trip_id", "headway_secs"])
    return {
        "stops": stops,
        "trips": trips,
        "stop_times": stop_times,
        "frequencies": frequencies,
    }
