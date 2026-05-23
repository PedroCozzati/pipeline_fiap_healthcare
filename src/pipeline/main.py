from pathlib import Path
import argparse

from src.pipeline.ingest import (
    load_pns_data,
    load_od_data,
    load_shape_zones,
    load_ubs_geojson,
    load_gtfs_data,
)
from transform import (
    filter_pns_sp_capital,
    add_health_profile,
    add_travel_bucket,
    compute_pns_percent_table,
    build_work_route_matrix,
    get_top_routes,
    build_route_lines,
    build_vulnerability_buffers,
    compute_terminal_waits,
)
from output import save_dataframe_csv, save_geodataframe_geojson, ensure_dir


def run_pipeline(base_dir: Path, output_dir: Path):
    base_dir = Path(base_dir)
    output_dir = ensure_dir(output_dir)

    raw_dir = base_dir / "raw"
    pns_dir = raw_dir / "pns"
    od_dir = raw_dir / "od"
    gis_dir = raw_dir / "gis"
    gtfs_dir = raw_dir / "gtfs"

    pns_map = pns_dir / "input_PNS_2019.txt"
    pns_data = pns_dir / "PNS_2019.txt"
    od_sav = od_dir / "OD_2017_v1.sav"
    shape_zones = gis_dir / "Zonas_2017_region.shp"
    ubs_geojson = gis_dir / "geoportal_equipamento_saude_ubs_posto_centro_v2.geojson"
    stops_path = gtfs_dir / "stops.txt"
    trips_path = gtfs_dir / "trips.txt"
    stop_times_path = gtfs_dir / "stop_times.txt"
    frequencies_path = gtfs_dir / "frequencies.txt"

    target_vars = ["V0001", "V0031", "Q03001", "Q03201", "VDM001", "C008"]

    print("[1/5] Carregando PNS...")
    df_pns = load_pns_data(pns_map, pns_data, target_vars)
    df_pns = filter_pns_sp_capital(df_pns)
    df_pns = add_health_profile(df_pns)
    df_pns = add_travel_bucket(df_pns)

    print("[2/5] Gerando resumos PNS...")
    pns_summary = compute_pns_percent_table(df_pns)
    save_dataframe_csv(pns_summary, output_dir / "pns_summary.csv")

    print("[3/5] Carregando dados OD e geoespaciais...")
    df_od = load_od_data(od_sav)
    gdf_zones = load_shape_zones(shape_zones)
    gdf_ubs = load_ubs_geojson(ubs_geojson)

    print("[4/5] Construindo matriz de rotas e linhas...")
    route_matrix = build_work_route_matrix(df_od)
    top_routes = get_top_routes(route_matrix)
    save_dataframe_csv(top_routes, output_dir / "top_work_routes.csv")

    route_lines = build_route_lines(top_routes, gdf_zones)
    save_geodataframe_geojson(route_lines, output_dir / "top_work_route_lines.geojson")

    print("[5/5] Identificando vulnerabilidades e hubs de espera...")
    vulnerability = build_vulnerability_buffers(df_od, gdf_ubs)
    save_dataframe_csv(vulnerability, output_dir / "vulnerability_buffers.csv")

    gtfs = load_gtfs_data(stops_path, trips_path, stop_times_path, frequencies_path)
    terminals, critical_hubs = compute_terminal_waits(
        gtfs["stops"], gtfs["trips"], gtfs["stop_times"], gtfs["frequencies"]
    )
    save_dataframe_csv(terminals, output_dir / "terminal_waits.csv")
    save_dataframe_csv(critical_hubs, output_dir / "critical_hubs.csv")

    print("Pipeline concluída. Resultados salvos em:", output_dir)


def parse_args():
    parser = argparse.ArgumentParser(description="Executa o pipeline de descoberta de mobilidade e saúde.")
    parser.add_argument(
        "--base-dir",
        default=Path(__file__).resolve().parents[1],
        type=Path,
        help="Diretório base com os arquivos brutos de src.",
    )
    parser.add_argument(
        "--output-dir",
        default=Path(__file__).resolve().parents[1] / "output",
        type=Path,
        help="Diretório onde os resultados serão gravados.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(args.base_dir, args.output_dir)
