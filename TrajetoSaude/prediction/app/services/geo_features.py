import json
import logging
from functools import lru_cache
from math import atan2, cos, radians, sin, sqrt
from pathlib import Path
from typing import Optional

logger = logging.getLogger("prediction_ms")

RAIO_UBS_KM = 3.0
VELOCIDADE_MEDIA_KMH = 18.0   # média urbana considerando transporte público + caminhada até parada
FATOR_DESVIO_ROTA = 1.3       # ruas reais não seguem linha reta


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distância em km entre duas coordenadas, pela fórmula de haversine."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return 6371.0 * c


@lru_cache(maxsize=1)
def _carregar_pontos_ubs(geojson_path_str: str) -> tuple[tuple[float, float], ...]:
    """Carrega (latitude, longitude) de cada UBS do GeoJSON. Cacheado em memória por caminho."""
    path = Path(geojson_path_str)
    if not path.exists():
        logger.warning("Base de UBS não encontrada em %s — Qtd_UBS_Origem_3km usará fallback.", path)
        return ()

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    pontos: list[tuple[float, float]] = []
    for feature in data.get("features", []):
        geometry = feature.get("geometry") or {}
        coords = geometry.get("coordinates")
        if not coords or len(coords) < 2:
            continue
        try:
            lon, lat = float(coords[0]), float(coords[1])
        except (TypeError, ValueError):
            continue
        pontos.append((lat, lon))
    return tuple(pontos)


def contar_ubs_no_raio(lat: float, lon: float, geojson_path: Path, raio_km: float = RAIO_UBS_KM) -> Optional[int]:
    """Conta UBS num raio a partir de um ponto. None se a base geográfica não estiver disponível."""
    pontos = _carregar_pontos_ubs(str(geojson_path))
    if not pontos:
        return None
    return sum(1 for plat, plon in pontos if haversine_distance(lat, lon, plat, plon) <= raio_km)


def estimar_tempo_deslocamento_min(
    lat_residencia: float,
    lon_residencia: float,
    lat_trabalho: Optional[float] = None,
    lon_trabalho: Optional[float] = None,
) -> float:
    """Estima o tempo de deslocamento diário (somente ida) pela distância residência → trabalho."""
    if lat_trabalho is None or lon_trabalho is None:
        return 0.0
    distancia_km = haversine_distance(lat_residencia, lon_residencia, lat_trabalho, lon_trabalho) * FATOR_DESVIO_ROTA
    return round((distancia_km / VELOCIDADE_MEDIA_KMH) * 60, 1)
