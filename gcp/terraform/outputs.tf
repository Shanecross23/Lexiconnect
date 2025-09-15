output "backend_url" {
  description = "URL of the deployed backend service"
  value       = google_cloud_run_service.backend.status[0].url
}

output "neo4j_ip" {
  description = "Neo4j instance external IP"
  value       = google_compute_instance.neo4j.network_interface[0].access_config[0].nat_ip
}

output "neo4j_uri" {
  description = "Neo4j connection URI"
  value       = "bolt://${google_compute_instance.neo4j.network_interface[0].access_config[0].nat_ip}:7687"
}

output "storage_bucket_name" {
  description = "Name of the Cloud Storage bucket"
  value       = google_storage_bucket.uploads.name
}

output "project_id" {
  description = "GCP Project ID"
  value       = var.project_id
}
