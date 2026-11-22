resource "aws_s3_bucket" "records" {
  bucket = "records"
}
resource "aws_s3_bucket_acl" "records" {
  bucket = aws_s3_bucket.records.id
  acl = "public-read"
}
resource "aws_ecs_task_definition" "app" {
  container_definitions = jsonencode([{ name = "app", environment = [{ name = "RECORDS_BUCKET", value = aws_s3_bucket.records.id }] }])
}
