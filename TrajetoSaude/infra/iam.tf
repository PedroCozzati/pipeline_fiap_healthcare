resource "google_service_account" "app" {
     account_id   = var.service_account_id
     display_name = "Trajeto Saúde — aplicação"
     description  = "Service account usada pelos microserviços (Docker local ou Cloud Run)."

     depends_on = [google_project_service.apis]
}

resource "google_project_iam_member" "app_storage" {
     project = var.project_id
     role    = "roles/storage.objectAdmin"
     member  = "serviceAccount:${google_service_account.app.email}"
}

resource "google_project_iam_member" "app_cloudsql" {
     project = var.project_id
     role    = "roles/cloudsql.client"
     member  = "serviceAccount:${google_service_account.app.email}"
}

resource "google_project_iam_member" "app_vertex" {
     project = var.project_id
     role    = "roles/aiplatform.user"
     member  = "serviceAccount:${google_service_account.app.email}"
}

resource "google_service_account_key" "app" {
     count = var.create_sa_key ? 1 : 0

     service_account_id = google_service_account.app.name
}

resource "local_file" "sa_key" {
     count = var.create_sa_key ? 1 : 0

     content         = base64decode(google_service_account_key.app[0].private_key)
     filename        = "${path.module}/../credentials/gcp-sa.json"
     file_permission = "0600"
}
