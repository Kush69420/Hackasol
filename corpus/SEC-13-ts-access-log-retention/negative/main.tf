resource "aws_cloudwatch_log_group" "application" {
  name = "application"
  retention_in_days = 30
}
