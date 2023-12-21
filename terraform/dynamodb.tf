resource "aws_dynamodb_table" "iceman_tfstate_lock_table" {
  name         = "iceman-tfstate-lock-table"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"
  point_in_time_recovery {
    enabled = true
  }

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name        = "iceman-tfstate-lock-table"
    Environment = "Terraform"
  }
}
