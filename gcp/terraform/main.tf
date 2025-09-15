terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "containerregistry.googleapis.com",
    "compute.googleapis.com",
    "secretmanager.googleapis.com",
    "storage.googleapis.com"
  ])
  
  service = each.value
  project = var.project_id
}

# Neo4j instance on Compute Engine
resource "google_compute_instance" "neo4j" {
  name         = "lexiconnect-neo4j"
  machine_type = "e2-small"  # Reduced from e2-medium (saves ~$12/month)
  zone         = "${var.region}-a"
  
  depends_on = [
    google_project_service.apis
  ]
  
  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 10  # Reduced from 20GB (saves ~$2/month)
      type  = "pd-standard"  # Use standard persistent disk (cheaper than SSD)
    }
  }
  
  network_interface {
    network = "default"
    access_config {
      // Ephemeral IP (free, no static IP charges)
    }
  }
  
  # Enable auto-shutdown during development (optional)
  scheduling {
    preemptible         = true   # 80% cost savings but Google can restart the VM
    automatic_restart   = false  # Must be false when preemptible = true
    on_host_maintenance = "TERMINATE"  # Required for preemptible instances
  }
  
  metadata_startup_script = <<-EOF
    #!/bin/bash
    apt-get update
    apt-get install -y wget curl
    
    # Install Java
    apt-get install -y openjdk-11-jdk
    
    # Download and install Neo4j
    wget -O - https://debian.neo4j.com/neotechnology.gpg.key | apt-key add -
    echo 'deb https://debian.neo4j.com stable latest' | tee -a /etc/apt/sources.list.d/neo4j.list
    apt-get update
    apt-get install -y neo4j=1:5.14.0
    
    # Configure Neo4j
    sed -i 's/#server.default_listen_address=0.0.0.0/server.default_listen_address=0.0.0.0/' /etc/neo4j/neo4j.conf
    sed -i 's/#server.bolt.listen_address=:7687/server.bolt.listen_address=:7687/' /etc/neo4j/neo4j.conf
    sed -i 's/#server.http.listen_address=:7474/server.http.listen_address=:7474/' /etc/neo4j/neo4j.conf
    
    # Set initial password
    neo4j-admin set-initial-password ${var.neo4j_password}
    
    # Enable and start Neo4j
    systemctl enable neo4j
    systemctl start neo4j
  EOF
  
  tags = ["neo4j", "lexiconnect"]
}

# Firewall rule for Neo4j
resource "google_compute_firewall" "neo4j" {
  name    = "allow-neo4j"
  network = "default"
  
  depends_on = [
    google_project_service.apis
  ]
  
  allow {
    protocol = "tcp"
    ports    = ["7474", "7687"]
  }
  
  source_ranges = ["0.0.0.0/0"]  # Restrict this in production
  target_tags   = ["neo4j"]
}

# Cloud Storage bucket for file uploads
resource "google_storage_bucket" "uploads" {
  name     = "${var.project_id}-lexiconnect-uploads"
  location = var.region
  
  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    response_header = ["*"]
    max_age_seconds = 3600
  }
}

# Secret Manager for sensitive configuration
resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "jwt-secret-key"
  
  depends_on = [
    google_project_service.apis
  ]
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "jwt_secret_version" {
  secret      = google_secret_manager_secret.jwt_secret.id
  secret_data = var.jwt_secret_key
}

# Secret for Neo4j password
resource "google_secret_manager_secret" "neo4j_password" {
  secret_id = "neo4j-password"
  
  depends_on = [
    google_project_service.apis
  ]
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "neo4j_password_version" {
  secret      = google_secret_manager_secret.neo4j_password.id
  secret_data = var.neo4j_password
}

# Cloud Run service (will be deployed via Cloud Build)
resource "google_cloud_run_service" "backend" {
  name     = "lexiconnect-backend"
  location = var.region
  
  depends_on = [
    google_project_service.apis,
    google_compute_instance.neo4j
  ]
  
  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/lexiconnect-backend:latest"
        
        env {
          name  = "NEO4J_URI"
          value = "bolt://${google_compute_instance.neo4j.network_interface[0].access_config[0].nat_ip}:7687"
        }
        
        env {
          name  = "NEO4J_USER"
          value = "neo4j"
        }
        
        env {
          name = "NEO4J_PASSWORD"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.neo4j_password.secret_id
              key  = "latest"
            }
          }
        }
        
        env {
          name  = "GCP_PROJECT_ID"
          value = var.project_id
        }
        
        env {
          name  = "GCS_BUCKET_NAME"
          value = google_storage_bucket.uploads.name
        }
        
        env {
          name = "SECRET_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.jwt_secret.secret_id
              key  = "latest"
            }
          }
        }
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
}

# Make Cloud Run service publicly accessible
resource "google_cloud_run_service_iam_member" "allUsers" {
  service  = google_cloud_run_service.backend.name
  location = google_cloud_run_service.backend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Get project number for the default compute service account
data "google_project" "project" {
  project_id = var.project_id
}

# Grant Cloud Run service account access to Secret Manager
resource "google_project_iam_member" "cloud_run_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}
