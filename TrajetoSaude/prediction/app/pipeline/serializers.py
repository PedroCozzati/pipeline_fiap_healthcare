import base64
import io
from pathlib import Path

import geopandas as gpd
import joblib
import pandas as pd


def ensure_dir(path: Path) -> Path:
     path = Path(path)
     path.mkdir(parents=True, exist_ok=True)
     return path


def dataframe_to_csv(df: pd.DataFrame) -> str:
     return df.to_csv(index=True)


def geodataframe_to_geojson(gdf: gpd.GeoDataFrame) -> str:
     buffer = io.BytesIO()
     gdf.to_file(buffer, driver="GeoJSON")
     return buffer.getvalue().decode("utf-8")


def model_to_base64(model) -> str:
     buffer = io.BytesIO()
     joblib.dump(model, buffer)
     return base64.b64encode(buffer.getvalue()).decode("ascii")
