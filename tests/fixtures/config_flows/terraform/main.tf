provider "aws" {
  region = var.region
}
resource "aws_efs_file_system" "data" {}
resource "aws_cloudwatch_log_group" "other" {
  retention_in_days = 30
}
