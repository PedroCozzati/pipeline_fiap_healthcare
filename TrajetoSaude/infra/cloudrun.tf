# Cloud Run — execução dos microserviços diretamente no GCP (sem Docker local).
#
# Fluxo de uso (ver scripts/deploy-cloudrun.ps1 ou .sh):
#   1. terraform apply (deploy_cloud_run=false) → cria Artifact Registry + infra base
#   2. build & push das imagens para o Artifact Registry
#   3. terraform apply -var="deploy_cloud_run=true" → cria os serviços Cloud Run

resource "google_artifact_registry_repository" "app" {
     location      = var.region
     repository_id = "trajeto-saude"
     description   = "Imagens Docker dos microserviços Trajeto Saúde"
     format        = "DOCKER"

     depends_on = [google_project_service.apis]
}

resource "random_password" "jwt_secret" {
     length  = 32
     special = false
}

locals {
     image_registry = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.app.repository_id}"
}

# ── Auth ──────────────────────────────────────────────────────────────────

resource "google_cloud_run_v2_service" "auth" {
     count    = var.deploy_cloud_run ? 1 : 0
     name     = "trajeto-auth"
     location = var.region
     ingress  = "INGRESS_TRAFFIC_ALL"

     template {
          service_account = google_service_account.app.email

          scaling {
               min_instance_count = var.cloud_run_min_instances
               max_instance_count = var.cloud_run_max_instances
          }

          containers {
               image = "${local.image_registry}/auth:${var.image_tag}"

               ports {
                    container_port = 8003
               }

               env {
                    name  = "CLOUD_SQL_INSTANCE_CONNECTION_NAME"
                    value = google_sql_database_instance.main.connection_name
               }
               env {
                    name  = "CLOUD_SQL_DATABASE"
                    value = google_sql_database.app.name
               }
               env {
                    name  = "CLOUD_SQL_USER"
                    value = google_sql_user.app.name
               }
               env {
                    name  = "CLOUD_SQL_PASSWORD"
                    value = random_password.db_password.result
               }
               env {
                    name  = "JWT_SECRET_KEY"
                    value = random_password.jwt_secret.result
               }
               env {
                    name  = "GCP_PROJECT_ID"
                    value = var.project_id
               }
          }
     }

     depends_on = [google_artifact_registry_repository.app]
}

resource "google_cloud_run_v2_service_iam_member" "auth_public" {
     count    = var.deploy_cloud_run ? 1 : 0
     project  = var.project_id
     location = var.region
     name     = google_cloud_run_v2_service.auth[0].name
     role     = "roles/run.invoker"
     member   = "allUsers"
}

# ── Storage ───────────────────────────────────────────────────────────────

resource "google_cloud_run_v2_service" "storage" {
     count    = var.deploy_cloud_run ? 1 : 0
     name     = "trajeto-storage"
     location = var.region
     ingress  = "INGRESS_TRAFFIC_ALL"

     template {
          service_account = google_service_account.app.email

          scaling {
               min_instance_count = var.cloud_run_min_instances
               max_instance_count = var.cloud_run_max_instances
          }

          containers {
               image = "${local.image_registry}/storage:${var.image_tag}"

               ports {
                    container_port = 8001
               }

               env {
                    name  = "CLOUD_SQL_INSTANCE_CONNECTION_NAME"
                    value = google_sql_database_instance.main.connection_name
               }
               env {
                    name  = "CLOUD_SQL_DATABASE"
                    value = google_sql_database.app.name
               }
               env {
                    name  = "CLOUD_SQL_USER"
                    value = google_sql_user.app.name
               }
               env {
                    name  = "CLOUD_SQL_PASSWORD"
                    value = random_password.db_password.result
               }
               env {
                    name  = "GCS_BUCKET_NAME"
                    value = google_storage_bucket.data.name
               }
               env {
                    name  = "GCS_ARTIFACTS_PREFIX"
                    value = var.gcs_artifacts_prefix
               }
               env {
                    name  = "GCP_PROJECT_ID"
                    value = var.project_id
               }
          }
     }

     depends_on = [google_artifact_registry_repository.app]
}

resource "google_cloud_run_v2_service_iam_member" "storage_public" {
     count    = var.deploy_cloud_run ? 1 : 0
     project  = var.project_id
     location = var.region
     name     = google_cloud_run_v2_service.storage[0].name
     role     = "roles/run.invoker"
     member   = "allUsers"
}

# ── Prediction ────────────────────────────────────────────────────────────

resource "google_cloud_run_v2_service" "prediction" {
     count    = var.deploy_cloud_run ? 1 : 0
     name     = "trajeto-prediction"
     location = var.region
     ingress  = "INGRESS_TRAFFIC_ALL"

     template {
          service_account = google_service_account.app.email
          timeout         = "600s"

          scaling {
               min_instance_count = var.cloud_run_min_instances
               max_instance_count = var.cloud_run_max_instances
          }

          containers {
               image = "${local.image_registry}/prediction:${var.image_tag}"

               ports {
                    container_port = 8002
               }

               resources {
                    limits = {
                         cpu    = "2"
                         memory = "2Gi"
                    }
               }

               env {
                    name  = "STORAGE_SERVICE_URL"
                    value = google_cloud_run_v2_service.storage[0].uri
               }
               env {
                    name  = "GCS_BUCKET_NAME"
                    value = google_storage_bucket.data.name
               }
               env {
                    name  = "GCS_ARTIFACTS_PREFIX"
                    value = var.gcs_artifacts_prefix
               }
               env {
                    name  = "MODEL_SOURCE"
                    value = "gcs"
               }
               env {
                    name  = "MODEL_GCS_URI"
                    value = "gs://${google_storage_bucket.data.name}/${var.gcs_artifacts_prefix}risk_model.joblib"
               }
               env {
                    name  = "GCP_PROJECT_ID"
                    value = var.project_id
               }
          }
     }

     depends_on = [google_artifact_registry_repository.app]
}

resource "google_cloud_run_v2_service_iam_member" "prediction_public" {
     count    = var.deploy_cloud_run ? 1 : 0
     project  = var.project_id
     location = var.region
     name     = google_cloud_run_v2_service.prediction[0].name
     role     = "roles/run.invoker"
     member   = "allUsers"
}

# ── Sentinel (Vertex AI) ──────────────────────────────────────────────────

resource "google_cloud_run_v2_service" "sentinel" {
     count    = var.deploy_cloud_run ? 1 : 0
     name     = "trajeto-sentinel"
     location = var.region
     ingress  = "INGRESS_TRAFFIC_ALL"

     template {
          service_account = google_service_account.app.email
          timeout         = "300s"

          scaling {
               min_instance_count = var.cloud_run_min_instances
               max_instance_count = var.cloud_run_max_instances
          }

          containers {
               image = "${local.image_registry}/sentinel:${var.image_tag}"

               ports {
                    container_port = 8004
               }

               env {
                    name  = "GCP_PROJECT_ID"
                    value = var.project_id
               }
               env {
                    name  = "GCP_REASONING_ENGINE_URL"
                    value = local.agent_engine_query_urls["sentinela_ai"]
               }
               env {
                    name  = "GCP_REASONING_ENGINE_AGENTE_URL"
                    value = local.agent_engine_query_urls["sentinela_ai_agentedesaude"]
               }
               env {
                    name  = "GCP_REASONING_ENGINE_UBS_PER_3KM_URL"
                    value = local.agent_engine_query_urls["sentinel_ai_ubs_per_3km"]
               }
          }
     }

     depends_on = [google_artifact_registry_repository.app]
}

resource "google_cloud_run_v2_service_iam_member" "sentinel_public" {
     count    = var.deploy_cloud_run ? 1 : 0
     project  = var.project_id
     location = var.region
     name     = google_cloud_run_v2_service.sentinel[0].name
     role     = "roles/run.invoker"
     member   = "allUsers"
}

# ── Gateway ───────────────────────────────────────────────────────────────

resource "google_cloud_run_v2_service" "gateway" {
     count    = var.deploy_cloud_run ? 1 : 0
     name     = "trajeto-gateway"
     location = var.region
     ingress  = "INGRESS_TRAFFIC_ALL"

     template {
          service_account = google_service_account.app.email
          timeout         = "300s"

          scaling {
               min_instance_count = var.cloud_run_min_instances
               max_instance_count = var.cloud_run_max_instances
          }

          containers {
               image = "${local.image_registry}/gateway:${var.image_tag}"

               ports {
                    container_port = 8000
               }

               env {
                    name  = "AUTH_SERVICE_URL"
                    value = google_cloud_run_v2_service.auth[0].uri
               }
               env {
                    name  = "STORAGE_SERVICE_URL"
                    value = google_cloud_run_v2_service.storage[0].uri
               }
               env {
                    name  = "PREDICTION_SERVICE_URL"
                    value = google_cloud_run_v2_service.prediction[0].uri
               }
               env {
                    name  = "SENTINEL_SERVICE_URL"
                    value = google_cloud_run_v2_service.sentinel[0].uri
               }
               env {
                    # Restrinja ao domínio do frontend após o primeiro deploy, se necessário.
                    name  = "CORS_ORIGINS"
                    value = "[\"*\"]"
               }
          }
     }

     depends_on = [google_artifact_registry_repository.app]
}

resource "google_cloud_run_v2_service_iam_member" "gateway_public" {
     count    = var.deploy_cloud_run ? 1 : 0
     project  = var.project_id
     location = var.region
     name     = google_cloud_run_v2_service.gateway[0].name
     role     = "roles/run.invoker"
     member   = "allUsers"
}

# ── Frontend ──────────────────────────────────────────────────────────────

resource "google_cloud_run_v2_service" "frontend" {
     count    = var.deploy_cloud_run ? 1 : 0
     name     = "trajeto-frontend"
     location = var.region
     ingress  = "INGRESS_TRAFFIC_ALL"

     template {
          service_account = google_service_account.app.email

          scaling {
               min_instance_count = var.cloud_run_min_instances
               max_instance_count = var.cloud_run_max_instances
          }

          containers {
               image = "${local.image_registry}/frontend:${var.image_tag}"

               ports {
                    container_port = 80
               }

               env {
                    name  = "GATEWAY_URL"
                    value = google_cloud_run_v2_service.gateway[0].uri
               }
          }
     }

     depends_on = [google_artifact_registry_repository.app]
}

resource "google_cloud_run_v2_service_iam_member" "frontend_public" {
     count    = var.deploy_cloud_run ? 1 : 0
     project  = var.project_id
     location = var.region
     name     = google_cloud_run_v2_service.frontend[0].name
     role     = "roles/run.invoker"
     member   = "allUsers"
}
