terraform {
  required_version = "~> 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~>5.23.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~>2.4.0"
    }
    }
    backend "s3" {
      bucket         = "iceman-tfstate-dev"
      key            = "./terraform.tfstate"
      region         = "eu-west-2"
      dynamodb_table = "iceman-tfstate-lock-table"
      encrypt        = true
    }
}

provider "aws" {
  region = var.region
}

module "iam" {
  source  = "terraform-aws-modules/iam/aws"
  version = "5.30.1"
}

#module "notify_slack" {
#  #checkov:skip=CKV_TF_1: "Ensure Terraform module sources use a commit hash"
#  source            = "terraform-aws-modules/notify-slack/aws"
#  version           = "6.0.0"
#  slack_webhook_url = var.slack_webhook
#  sns_topic_name    = "iceman-slack-alert"
#  slack_channel     = "alerts"
#  slack_username    = "reporter"
#}

data "aws_ssoadmin_instances" "current" {}

data "aws_caller_identity" "current" {}

data "aws_iam_role" "iceman_lambda_role" {
  name = "iceman-lambda-role"
}

output "iam_role_arn" {
  value = data.aws_iam_role.iceman_lambda_role.arn
}
