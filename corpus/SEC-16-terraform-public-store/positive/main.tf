resource "aws_db_instance" "accounts" {
  engine = "postgres"
  publicly_accessible = true
  vpc_security_group_ids = [aws_security_group.database.id]
}
resource "aws_security_group" "database" {
  ingress {
    from_port = 5432
    to_port = 5432
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
resource "aws_ecs_task_definition" "app" {
  container_definitions = jsonencode([{ name = "app", environment = [{ name = "DATABASE_HOST", value = aws_db_instance.accounts.address }] }])
}
