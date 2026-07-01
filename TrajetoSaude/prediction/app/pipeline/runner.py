from pathlib import Path

from app.config import resolve_pipeline_base_dir, settings
from app.pipeline.ingest import (
     load_gtfs_data,
     load_od_data,
     load_pns_data,
     load_shape_zones,
     load_ubs_geojson,
)
from app.pipeline.serializers import (
     dataframe_to_csv,
     geodataframe_to_geojson,
     model_to_base64,
)
from app.pipeline.train import DEFAULT_FEATURE_COLUMNS, resolve_training_data, train_risk_model
from app.pipeline.transform import (
     add_health_profile,
     add_travel_bucket,
     build_route_lines,
     build_vulnerability_buffers,
     build_work_route_matrix,
     compute_pns_percent_table,
     compute_terminal_waits,
     filter_pns_sp_capital,
     get_top_routes,
)
from app.services.storage_client import StorageServiceClient


PIPELINE_OUTPUTS = [
     ("pns_summary.csv", "text/csv", "text"),
     ("top_work_routes.csv", "text/csv", "text"),
     ("top_work_route_lines.geojson", "application/geo+json", "text"),
     ("vulnerability_buffers.csv", "text/csv", "text"),
     ("terminal_waits.csv", "text/csv", "text"),
     ("critical_hubs.csv", "text/csv", "text"),
     ("risk_training.csv", "text/csv", "text"),
     ("risk_model.joblib", "application/octet-stream", "base64"),
]

RAW_FILE_LAYOUT = """
TrajetoSaude/data/raw/
├── pns/input_PNS_2019.txt
├── pns/PNS_2019.txt
├── od/OD_2017_v1.sav
├── gis/Zonas_2017_region.shp (+ .dbf, .shx, .prj, .cpg)
├── gis/geoportal_equipamento_saude_ubs_posto_centro_v2.geojson
└── gtfs/stops.txt, trips.txt, stop_times.txt, frequencies.txt
""".strip()

TARGET_VARS = ["V0001", "V0031", "Q03001", "Q03201", "VDM001", "C008"]


def _resolve_raw_paths(base_dir: Path) -> dict[str, Path]:
     raw_dir = base_dir / "raw"
     return {
          "pns_map": raw_dir / "pns" / "input_PNS_2019.txt",
          "pns_data": raw_dir / "pns" / "PNS_2019.txt",
          "od_sav": raw_dir / "od" / "OD_2017_v1.sav",
          "shape_zones": raw_dir / "gis" / "Zonas_2017_region.shp",
          "ubs_geojson": raw_dir / "gis" / "geoportal_equipamento_saude_ubs_posto_centro_v2.geojson",
          "stops": raw_dir / "gtfs" / "stops.txt",
          "trips": raw_dir / "gtfs" / "trips.txt",
          "stop_times": raw_dir / "gtfs" / "stop_times.txt",
          "frequencies": raw_dir / "gtfs" / "frequencies.txt",
     }


def _validate_raw_files(paths: dict[str, Path]) -> list[str]:
     return [name for name, path in paths.items() if not path.exists()]


def _artifact_blob_name(filename: str) -> str:
     prefix = settings.gcs_artifacts_prefix.strip("/")
     if prefix:
          return f"{prefix}/{filename}"
     return filename


def run_ingestion_pipeline(
     base_dir: Path | None = None,
     storage_client: StorageServiceClient | None = None,
) -> dict:
     base_dir = Path(base_dir) if base_dir else resolve_pipeline_base_dir()
     output_dir = base_dir / "output"
     storage = storage_client or StorageServiceClient()

     raw_paths = _resolve_raw_paths(base_dir)
     missing = _validate_raw_files(raw_paths)
     if missing:
          missing_paths = [f"  - {raw_paths[name]}" for name in missing]
          raise FileNotFoundError(
               f"Dados brutos ausentes em {base_dir / 'raw'}.\n"
               f"Arquivos faltando ({len(missing)}):\n"
               + "\n".join(missing_paths)
               + f"\n\nEstrutura esperada dentro de TrajetoSaude:\n{RAW_FILE_LAYOUT}"
          )

     steps: list[str] = []
     artifacts: dict[str, str] = {}

     steps.append("Carregando e transformando PNS")
     df_pns = load_pns_data(raw_paths["pns_map"], raw_paths["pns_data"], TARGET_VARS)
     df_pns = filter_pns_sp_capital(df_pns)
     df_pns = add_health_profile(df_pns)
     df_pns = add_travel_bucket(df_pns)
     pns_summary = compute_pns_percent_table(df_pns)
     artifacts["pns_summary.csv"] = dataframe_to_csv(pns_summary)

     steps.append("Carregando OD, zonas e UBS")
     df_od = load_od_data(raw_paths["od_sav"])
     gdf_zones = load_shape_zones(raw_paths["shape_zones"])
     gdf_ubs = load_ubs_geojson(raw_paths["ubs_geojson"])

     steps.append("Construindo matriz de rotas")
     route_matrix = build_work_route_matrix(df_od)
     top_routes = get_top_routes(route_matrix)
     artifacts["top_work_routes.csv"] = dataframe_to_csv(top_routes)

     route_lines = build_route_lines(top_routes, gdf_zones)
     artifacts["top_work_route_lines.geojson"] = geodataframe_to_geojson(route_lines)

     steps.append("Calculando vulnerabilidades e hubs")
     vulnerability = build_vulnerability_buffers(df_od, gdf_ubs)
     artifacts["vulnerability_buffers.csv"] = dataframe_to_csv(vulnerability)

     gtfs = load_gtfs_data(
          raw_paths["stops"],
          raw_paths["trips"],
          raw_paths["stop_times"],
          raw_paths["frequencies"],
     )
     terminals, critical_hubs = compute_terminal_waits(
          gtfs["stops"], gtfs["trips"], gtfs["stop_times"], gtfs["frequencies"]
     )
     artifacts["terminal_waits.csv"] = dataframe_to_csv(terminals)
     artifacts["critical_hubs.csv"] = dataframe_to_csv(critical_hubs)

     steps.append("Treinando modelo de risco")
     training_df, training_source = resolve_training_data(output_dir)
     artifacts["risk_training.csv"] = dataframe_to_csv(training_df)
     model, accuracy = train_risk_model(training_df, feature_columns=DEFAULT_FEATURE_COLUMNS)
     artifacts["risk_model.joblib"] = model_to_base64(model)

     steps.append("Enviando artefatos ao GCS via storage MS")
     uploads: list[dict] = []
     content_types = {name: ctype for name, ctype, _ in PIPELINE_OUTPUTS}
     encodings = {name: enc for name, _, enc in PIPELINE_OUTPUTS}

     for filename, content in artifacts.items():
          blob_name = _artifact_blob_name(filename)
          if encodings[filename] == "base64":
               result = storage.upload_base64(blob_name, content, content_types[filename])
          else:
               result = storage.upload_text(blob_name, content, content_types[filename])
          uploads.append({
               "filename": filename,
               "blob_name": result.get("name", blob_name),
               "bucket": result.get("bucket"),
               "status": result.get("status", "uploaded"),
          })

     return {
          "status": "completed",
          "base_dir": str(base_dir),
          "gcs_prefix": settings.gcs_artifacts_prefix,
          "steps": steps,
          "training_source": training_source,
          "model_validation_accuracy": accuracy,
          "uploads": uploads,
          "upload_count": len(uploads),
     }
