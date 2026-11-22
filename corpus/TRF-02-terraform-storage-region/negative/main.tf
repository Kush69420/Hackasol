provider "aws" {
  region = var.aws_region
}
variable "aws_region" {
  default = "ap-south-1"
}
resource "aws_efs_file_system" "data" {
  encrypted = true
}
