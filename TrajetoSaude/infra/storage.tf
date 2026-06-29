resource "google_storage_bucket" "data" {
     name     = local.bucket_name
     location = var.region
     project  = var.project_id

     uniform_bucket_level_access = true
     force_destroy               = true

     versioning {
          enabled = true
     }

     depends_on = [google_project_service.apis]
}
