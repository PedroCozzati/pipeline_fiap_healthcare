provider "google" {
     project = var.project_id
     region  = var.region
}

resource "random_id" "bucket_suffix" {
     byte_length = 4
}

locals {
     bucket_name = var.gcs_bucket_name != "" ? var.gcs_bucket_name : "${var.project_id}-trajeto-${random_id.bucket_suffix.hex}"
     sa_email    = "${var.service_account_id}@${var.project_id}.iam.gserviceaccount.com"

     required_apis = [
          "storage.googleapis.com",
          "sqladmin.googleapis.com",
          "iam.googleapis.com",
          "iamcredentials.googleapis.com",
          "serviceusage.googleapis.com",
          "aiplatform.googleapis.com",
          "run.googleapis.com",
          "artifactregistry.googleapis.com",
          "cloudbuild.googleapis.com",
     ]
}

resource "google_project_service" "apis" {
     for_each = toset(local.required_apis)

     project            = var.project_id
     service            = each.value
     disable_on_destroy = false
}
