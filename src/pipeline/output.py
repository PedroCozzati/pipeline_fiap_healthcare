from pathlib import Path
import pandas as pd
import geopandas as gpd


def ensure_dir(path: Path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_dataframe_csv(df: pd.DataFrame, path: Path):
    path = Path(path)
    ensure_dir(path.parent)
    df.to_csv(path, index=True)
    return path


def save_geodataframe_geojson(gdf: gpd.GeoDataFrame, path: Path):
    path = Path(path)
    ensure_dir(path.parent)
    gdf.to_file(path, driver="GeoJSON")
    return path


def save_report_text(text: str, path: Path):
    path = Path(path)
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")
    return path
