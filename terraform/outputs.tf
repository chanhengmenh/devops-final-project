output "public_ip" {
  description = "EC2 instance public IP"
  value       = aws_instance.app.public_ip
}

output "app_url" {
  description = "Application URL"
  value       = "http://${aws_instance.app.public_ip}:8000"
}

output "grafana_url" {
  description = "Grafana URL"
  value       = "http://${aws_instance.app.public_ip}:3000"
}

output "prometheus_url" {
  description = "Prometheus URL"
  value       = "http://${aws_instance.app.public_ip}:9090"
}
