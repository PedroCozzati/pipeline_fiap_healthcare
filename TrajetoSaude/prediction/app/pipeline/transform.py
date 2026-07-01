from pathlib import Path
import re
import unicodedata
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, LineString


def _normalize_motivation(value):
    return str(value).strip()


def filter_pns_sp_capital(df: pd.DataFrame, state: str = "35", capital: str = "1", diabetes_code: str = "1"):
    return df[(df["V0001"] == state) & (df["V0031"] == capital) & (df["Q03001"] == diabetes_code)].copy()


def add_health_profile(df: pd.DataFrame):
    df = df.copy()
    df["Rotina_de_Trabalho"] = np.where(
        df["VDM001"].isin([None, "", "nan"]) | df["VDM001"].isna(),
        "Não se desloca (Home Office ou Inativo)",
        "Trabalha presencialmente (Enfrenta deslocamento)"
    )

    legenda = {
        "1": "Preventivo (Sim, regularmente)",
        "2": "Reativo (Não, só quando há problemas)",
        "3": "Negligente (Nunca vai ao médico)",
    }
    df["Perfil_de_Acompanhamento"] = df["Q03201"].astype(str).map(legenda)
    return df


def add_travel_bucket(df: pd.DataFrame):
    df = df.copy()
    faixas_tempo = {
        "1": "A. Menos de 30 min",
        "2": "B. Entre 30 min e 1 hora",
        "3": "C. Entre 1 hora e 2 horas",
        "4": "D. Mais de 2 horas",
        "nan": "E. Não se desloca (Trabalha em Casa/Inativo)",
    }
    df["VDM001"] = df["VDM001"].astype(str).replace("", "nan")
    df["Faixa_Deslocamento"] = df["VDM001"].map(faixas_tempo).fillna("E. Não se desloca (Trabalha em Casa/Inativo)")
    return df


def compute_pns_percent_table(df: pd.DataFrame, index: str = "Rotina_de_Trabalho"):
    resultado = pd.crosstab(
        df[index],
        df["Perfil_de_Acompanhamento"],
        normalize="index"
    ) * 100
    return resultado.round(1)


def build_work_route_matrix(df_od: pd.DataFrame, min_volume: int = 1000):
    df = df_od.copy()
    motivos_origem = [8, "8", 8.0]
    motivos_destino = [1, 2, 3, "1", "2", "3", 1.0, 2.0, 3.0]

    df = df[df["motivo_o"].isin(motivos_origem) & df["motivo_d"].isin(motivos_destino)]
    df = df[["zona_o", "zona_d", "duracao", "fe_via"]].dropna()
    df["zona_o"] = df["zona_o"].astype(int)
    df["zona_d"] = df["zona_d"].astype(int)

    matriz_rotas = df.groupby(["zona_o", "zona_d"]).agg(
        Tempo_Medio=("duracao", "mean"),
        Volume_Pessoas=("fe_via", "sum")
    ).reset_index()
    return matriz_rotas[matriz_rotas["Volume_Pessoas"] > min_volume].copy()


def get_top_routes(matriz_rotas: pd.DataFrame, top_n: int = 30):
    return matriz_rotas.sort_values(by="Tempo_Medio", ascending=False).head(top_n).copy()


def build_route_lines(top_routes: pd.DataFrame, gdf_zones: gpd.GeoDataFrame):
    if "NumeroZona" not in gdf_zones.columns:
        raise ValueError("O GeoDataFrame de zonas deve conter a coluna NumeroZona.")

    gdf_zones = gdf_zones.copy()
    gdf_zones["centroid"] = gdf_zones.geometry.centroid
    dict_centroides = gdf_zones.set_index("NumeroZona")["centroid"].to_dict()

    linhas = []
    for _, row in top_routes.iterrows():
        origem = int(row["zona_o"])
        destino = int(row["zona_d"])
        if origem == destino:
            continue
        if origem in dict_centroides and destino in dict_centroides:
            ponto_a = dict_centroides[origem]
            ponto_b = dict_centroides[destino]
            linhas.append({
                "zona_o": origem,
                "zona_d": destino,
                "Tempo_Medio": row["Tempo_Medio"],
                "Volume_Pessoas": row["Volume_Pessoas"],
                "geometry": LineString([ponto_a, ponto_b]),
            })

    gdf_linhas = gpd.GeoDataFrame(linhas, crs=gdf_zones.crs)
    return gdf_linhas


def build_vulnerability_buffers(
    df_od: pd.DataFrame,
    gdf_ubs: gpd.GeoDataFrame,
    buffer_meters: int = 3000,
    min_volume: int = 50,
    min_duration: int = 90,
):
    if not {"co_o_x", "co_o_y", "co_d_x", "co_d_y", "duracao", "fe_via"}.issubset(df_od.columns):
        raise ValueError("O DataFrame OD precisa conter as colunas co_o_x, co_o_y, co_d_x, co_d_y, duracao e fe_via.")

    df = df_od.copy()
    df = df[(df["duracao"] >= min_duration) & (df["fe_via"] > min_volume)].dropna(
        subset=["co_o_x", "co_o_y", "co_d_x", "co_d_y"]
    )

    df["pt_origem"] = df.apply(lambda row: Point(row["co_o_x"], row["co_o_y"]), axis=1)
    df["pt_destino"] = df.apply(lambda row: Point(row["co_d_x"], row["co_d_y"]), axis=1)

    gdf_origens = gpd.GeoDataFrame(df, geometry="pt_origem", crs=gdf_ubs.crs)
    gdf_destinos = gpd.GeoDataFrame(df, geometry="pt_destino", crs=gdf_ubs.crs)

    gdf_origens = gdf_origens.set_geometry(gdf_origens.geometry.buffer(buffer_meters))
    gdf_destinos = gdf_destinos.set_geometry(gdf_destinos.geometry.buffer(buffer_meters))

    ubs_na_casa = gpd.sjoin(gdf_ubs, gdf_origens, how="inner", predicate="within")
    ubs_no_trab = gpd.sjoin(gdf_ubs, gdf_destinos, how="inner", predicate="within")

    contagem_casa = ubs_na_casa.groupby(ubs_na_casa.index_right).size()
    contagem_trab = ubs_no_trab.groupby(ubs_no_trab.index_right).size()

    df_result = df.copy()
    df_result["UBS_a_Pe_da_Casa"] = df_result.index.map(contagem_casa).fillna(0).astype(int)
    df_result["UBS_a_Pe_do_Trab"] = df_result.index.map(contagem_trab).fillna(0).astype(int)
    return df_result


def _normalize_terminal_name(nome: str) -> str:
    if not isinstance(nome, str):
        return ""
    nome = unicodedata.normalize("NFD", nome)
    nome = "".join(c for c in nome if unicodedata.category(c) != "Mn")
    nome = nome.upper()
    nome = nome.replace("TERM.", "TERMINAL").replace("EST.", "ESTACAO")
    nome = re.split(r"[-|,|\(]", nome)[0].strip()
    return " ".join(nome.split())


def compute_terminal_waits(stops: pd.DataFrame, trips: pd.DataFrame, stop_times: pd.DataFrame, frequencies: pd.DataFrame, min_wait: int = 15):
    stops = stops.copy()
    stops["Nome_Limpo"] = stops["stop_name"].apply(_normalize_terminal_name)
    terminais = stops[stops["Nome_Limpo"].str.contains(r"TERMINAL|ESTACAO", na=False)].copy()

    trips_freq = trips.merge(frequencies, on="trip_id", how="inner")
    trips_freq["Espera_Media_Minutos"] = trips_freq["headway_secs"] / 120.0

    st_terminais = stop_times[stop_times["stop_id"].isin(terminais["stop_id"])]
    baldeacoes = st_terminais.merge(trips_freq, on="trip_id", how="inner")

    espera_por_terminal = baldeacoes.groupby("stop_id")["Espera_Media_Minutos"].mean().reset_index()
    terminais = terminais.merge(espera_por_terminal, on="stop_id", how="left")

    terminais_agrupados = terminais.groupby("Nome_Limpo").agg(
        stop_lat=("stop_lat", "mean"),
        stop_lon=("stop_lon", "mean"),
        Espera_Media_Minutos=("Espera_Media_Minutos", "mean"),
        Qtd_Plataformas=("stop_id", "nunique"),
    ).reset_index()

    terminais_agrupados["Espera_Media_Minutos"] = terminais_agrupados["Espera_Media_Minutos"].fillna(0)
    return terminais_agrupados, terminais_agrupados[terminais_agrupados["Espera_Media_Minutos"] >= min_wait].copy()
