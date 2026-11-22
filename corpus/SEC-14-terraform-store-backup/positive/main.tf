resource "aws_efs_file_system" "data" {
  encrypted = true
}
resource "aws_ecs_task_definition" "app" {
  container_definitions = jsonencode([{ mountPoints = [{ sourceVolume = "data", containerPath = "/app/sqlite" }] }])
  volume {
    name = "data"
    efs_volume_configuration { file_system_id = aws_efs_file_system.data.id }
  }
}
