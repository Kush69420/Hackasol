resource "aws_s3_bucket" "records" {
  bucket = "records"
}
resource "aws_s3_bucket_acl" "records" {
  bucket = aws_s3_bucket.records.id
  acl = "private"
}
resource "aws_s3_bucket_public_access_block" "records" {
  bucket = aws_s3_bucket.records.id
  block_public_acls = true
  ignore_public_acls = true
  block_public_policy = true
  restrict_public_buckets = true
}
resource "aws_ecs_task_definition" "app" {
  container_definitions = jsonencode([{ name = "app", environment = [{ name = "RECORDS_BUCKET", value = aws_s3_bucket.records.id }] }])
}
