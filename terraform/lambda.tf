locals {
  common_source_dir_prefix = "${path.module}/lambda-functions"
  functions = {
    "iceman-add-to-group"           = { handler = "iceman-add-to-group.lambda_handler" },
    "iceman-create-user"            = { handler = "iceman-create-user.lambda_handler" },
    "iceman-delete-user"            = { handler = "iceman-delete-user.lambda_handler" },
    "iceman-export-all-users"       = { handler = "iceman-export-all-users.lambda_handler" },
    "iceman-export-report"          = { handler = "iceman-export-report.lambda_handler" },
    "iceman-get-group-members"      = { handler = "iceman-get-group-members.lambda_handler" },
    "iceman-remove-from-all-groups" = { handler = "iceman-remove-from-all-groups.lambda_handler" },
    "iceman-remove-from-group"      = { handler = "iceman-remove-from-group.lambda_handler" }
  }
}

data "archive_file" "zip_lambdas" {
  for_each = local.functions

  type        = "zip"
  source_dir  = "${local.common_source_dir_prefix}/${each.key}/"
  output_path = "${path.module}/zips/${each.key}.zip"
}

resource "aws_lambda_function" "lambda" {
  for_each = local.functions

  function_name    = each.key
  filename         = data.archive_file.zip_lambdas[each.key].output_path
  source_code_hash = filebase64sha256(data.archive_file.zip_lambdas[each.key].output_path)
  role             = data.aws_iam_role.iceman_lambda_role.arn
  handler          = each.value.handler
  layers = [
    "arn:aws:lambda:eu-west-2:580247275435:layer:LambdaInsightsExtension:38",
    "arn:aws:lambda:eu-west-2:133256977650:layer:AWS-Parameters-and-Secrets-Lambda-Extension:11",
    "arn:aws:lambda:eu-west-2:336392948345:layer:AWSSDKPandas-Python311:4",
    "arn:aws:lambda:eu-west-2:017000801446:layer:AWSLambdaPowertoolsPythonV2:46"
  ]
  runtime = var.lambda_runtime

  environment {
    variables = var.lambda_environment_variables
  }

  tags = {
    Name        = title(replace(each.key, "-", " "))
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}
