provider "aws" {
  region = var.aws_region
}

resource "null_resource" "docker_build" {
  triggers = {
    dockerfile = filemd5("${path.module}/../../Dockerfile")
  }
  provisioner "local-exec" {
    # run the build from the repository root
    command = <<-EOT
      docker build -f ../infrastructure/Dockerfile ../ # unbalanced { brace inside a heredoc
    EOT
  }
}

resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${var.project_name}"
  retention_in_days = 30
}

resource "aws_security_group" "ecs" {
  name        = "fixture-ecs"
  description = "ECS tasks"
  # the "}" in this comment must not close the block
  ingress {
    from_port       = 3000
    to_port         = 3000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
