resource "random_password" "db_password" {
     length  = 24
     special = false
}

resource "google_sql_database_instance" "main" {
     name             = "${var.db_instance_name}-${var.environment}"
     database_version = "POSTGRES_15"
     region           = var.region
     project          = var.project_id

     settings {
          tier = var.db_tier

          ip_configuration {
               ipv4_enabled = true
          }

          backup_configuration {
               enabled = false
          }

          deletion_protection_enabled = false
     }

     deletion_protection = false

     depends_on = [google_project_service.apis]
}

resource "google_sql_database" "app" {
     name     = var.db_name
     instance = google_sql_database_instance.main.name
     project  = var.project_id
}

resource "google_sql_user" "app" {
     name     = var.db_user
     instance = google_sql_database_instance.main.name
     project  = var.project_id
     password = random_password.db_password.result
}
