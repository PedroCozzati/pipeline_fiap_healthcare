output "project_id" {
     description = "ID do projeto GCP."
     value       = var.project_id
}

output "region" {
     description = "Região GCP utilizada."
     value       = var.region
}

output "service_account_email" {
     description = "E-mail da service account da aplicação."
     value       = google_service_account.app.email
}

output "gcs_bucket_name" {
     description = "Nome do bucket GCS criado."
     value       = google_storage_bucket.data.name
}

output "gcs_artifacts_prefix" {
     description = "Prefixo dos artefatos no bucket."
     value       = var.gcs_artifacts_prefix
}

output "model_gcs_uri" {
     description = "URI GCS sugerida para o modelo de risco."
     value       = "gs://${google_storage_bucket.data.name}/${var.gcs_artifacts_prefix}risk_model.joblib"
}

output "cloud_sql_instance_connection_name" {
     description = "Connection name para o Cloud SQL Connector."
     value       = google_sql_database_instance.main.connection_name
}

output "cloud_sql_database" {
     description = "Nome do banco PostgreSQL."
     value       = google_sql_database.app.name
}

output "cloud_sql_user" {
     description = "Usuário do banco PostgreSQL."
     value       = google_sql_user.app.name
}

output "cloud_sql_password" {
     description = "Senha do banco PostgreSQL."
     value       = random_password.db_password.result
     sensitive   = true
}

output "sa_key_path" {
     description = "Caminho local da chave JSON (quando create_sa_key = true)."
     value       = var.create_sa_key ? abspath("${path.module}/../credentials/gcp-sa.json") : null
}

output "env_file_content" {
     description = "Conteúdo sugerido para o arquivo .env da aplicação."
     value       = <<-EOT
# Gerado automaticamente pelo Terraform — Trajeto Saúde
GCP_PROJECT_ID=${var.project_id}
GCP_REGION=${var.region}

GOOGLE_APPLICATION_CREDENTIALS=credentials/gcp-sa.json
GCP_SA_KEY_FILE=./credentials/gcp-sa.json

GCS_BUCKET_NAME=${google_storage_bucket.data.name}
GCS_ARTIFACTS_PREFIX=${var.gcs_artifacts_prefix}

CLOUD_SQL_INSTANCE_CONNECTION_NAME=${google_sql_database_instance.main.connection_name}
CLOUD_SQL_DATABASE=${google_sql_database.app.name}
CLOUD_SQL_USER=${google_sql_user.app.name}
CLOUD_SQL_PASSWORD=${random_password.db_password.result}

STORAGE_SERVICE_URL=http://storage:8001
PREDICTION_SERVICE_URL=http://prediction:8002
PIPELINE_BASE_DIR=data

MODEL_SOURCE=local
MODEL_GCS_URI=gs://${google_storage_bucket.data.name}/${var.gcs_artifacts_prefix}risk_model.joblib
MODEL_LOCAL_PATH=artefatos/risk_model.joblib

# Opcional — configure após criar o Reasoning Engine no Vertex AI
GCP_REASONING_ENGINE_URL=
GCP_REASONING_ENGINE_AGENTE_URL=

JWT_SECRET_KEY=altere-esta-chave-em-producao
CORS_ORIGINS=["http://localhost:4200"]
EOT
     sensitive = true
}
