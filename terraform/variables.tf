variable "common_tags" {
  type = map(string)
  default = {
    ManagedBy = "Terraform"
  }
}

variable "region" {
  default = "eu-west-2"
}

variable "environment" {
  default = "dev"
}

variable "lambda_runtime" {
  description = "The runtime environment for the Lambda function."
  type        = string
  default     = "python3.11"
}

variable "lambda_environment_variables" {
  description = "Environment variables for the lambda functions"
  type        = map(string)
  default     = {}
}

variable "slack_webhook" {
  type = string
}
