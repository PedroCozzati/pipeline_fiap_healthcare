variable "project_id" {
     description = "ID do projeto GCP (ex.: meu-projeto-123456)."
     type        = string
}

variable "region" {
     description = "Região GCP para Cloud SQL e demais recursos."
     type        = string
     default     = "us-central1"
}

variable "environment" {
     description = "Sufixo de ambiente (dev, staging, prod)."
     type        = string
     default     = "dev"
}

variable "db_instance_name" {
     description = "Nome da instância Cloud SQL."
     type        = string
     default     = "trajeto-db"
}

variable "db_name" {
     description = "Nome do banco PostgreSQL."
     type        = string
     default     = "trajeto_saude"
}

variable "db_user" {
     description = "Usuário do banco PostgreSQL."
     type        = string
     default     = "app_user"
}

variable "db_tier" {
     description = "Tier da instância Cloud SQL (db-f1-micro para demonstração)."
     type        = string
     default     = "db-f1-micro"
}

variable "gcs_bucket_name" {
     description = "Nome do bucket GCS (deve ser globalmente único). Deixe vazio para gerar automaticamente."
     type        = string
     default     = ""
}

variable "gcs_artifacts_prefix" {
     description = "Prefixo dos artefatos de modelo no bucket."
     type        = string
     default     = "model_evasao/v1/"
}

variable "create_sa_key" {
     description = "Gera chave JSON da service account em ../credentials/gcp-sa.json."
     type        = bool
     default     = true
}

variable "service_account_id" {
     description = "ID da service account da aplicação."
     type        = string
     default     = "trajeto-app"
}
