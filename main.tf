provider "aws" {
  region = var.region  # Use the declared region variable
}

resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false  # Ensure the suffix is lower case
}

resource "aws_s3_bucket" "lambda_bucket" {
  bucket = "izettleminbal-${random_string.suffix.result}"
}

resource "aws_s3_bucket_lifecycle_configuration" "lambda_bucket_lifecycle" {
  bucket = aws_s3_bucket.lambda_bucket.id

  rule {
    id     = "log-expiration"
    status = "Enabled"

    filter {
      prefix = "logs/"
    }

    expiration {
      days = var.log_expiration_days
    }
  }

  rule {
    id     = "screenshot-expiration"
    status = "Enabled"

    filter {
      prefix = "errors/"
    }

    expiration {
      days = var.screenshot_expiration_days
    }
  }
}

resource "aws_iam_role" "lambda_role" {
  name = "lambda_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      },
    ]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name   = "lambda_policy"
  role   = aws_iam_role.lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Effect   = "Allow"
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Action = [
          "s3:PutObject",
          "s3:GetObject"
        ]
        Effect   = "Allow"
        Resource = "arn:aws:s3:::${aws_s3_bucket.lambda_bucket.bucket}/*"
      }
    ]
  })
}

#resource "aws_iam_role" "api_gateway_cloudwatch_role" {
#  name = "api_gateway_cloudwatch_role"
#  assume_role_policy = jsonencode({
#    Version = "2012-10-17"
#    Statement = [
#      {
#        Effect = "Allow"
#        Principal = {
#          Service = "apigateway.amazonaws.com"
#        }
#        Action = "sts:AssumeRole"
#      },
#    ]
#  })
#}

#resource "aws_iam_role_policy" "api_gateway_cloudwatch_policy" {
#  name   = "api_gateway_cloudwatch_policy"
#  role   = aws_iam_role.api_gateway_cloudwatch_role.id
#  policy = jsonencode({
#    Version = "2012-10-17"
#    Statement = [
#      {
#        Effect = "Allow"
#        Action = [
#          "logs:CreateLogGroup",
#          "logs:CreateLogStream",
#          "logs:PutLogEvents"
#        ]
#        Resource = "arn:aws:logs:*:*:*"
#      }
#    ]
#  })
#}

#resource "aws_api_gateway_account" "api_gateway_account" {
#  cloudwatch_role_arn = aws_iam_role.api_gateway_cloudwatch_role.arn
#}

resource "aws_lambda_function" "izettleminbal" {
  filename         = "izettleminbal.zip"
  function_name    = "izettleminbal"
  role             = aws_iam_role.lambda_role.arn
  handler          = "izettleminbal.lambda_handler"
  source_code_hash = filebase64sha256("izettleminbal.zip")
  runtime          = "python3.8"
  environment {
    variables = {
      S3_BUCKET = aws_s3_bucket.lambda_bucket.bucket
    }
  }
}

resource "aws_api_gateway_rest_api" "izettleminbal_api" {
  name        = "izettleminbal_api"
  description = "API for updating iZettle minimum balance"
}

resource "aws_api_gateway_resource" "izettleminbal_resource" {
  rest_api_id = aws_api_gateway_rest_api.izettleminbal_api.id
  parent_id   = aws_api_gateway_rest_api.izettleminbal_api.root_resource_id
  path_part   = "update_balance"
}

resource "aws_api_gateway_method" "izettleminbal_method" {
  rest_api_id   = aws_api_gateway_rest_api.izettleminbal_api.id
  resource_id   = aws_api_gateway_resource.izettleminbal_resource.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "izettleminbal_integration" {
  rest_api_id = aws_api_gateway_rest_api.izettleminbal_api.id
  resource_id = aws_api_gateway_resource.izettleminbal_resource.id
  http_method = aws_api_gateway_method.izettleminbal_method.http_method
  integration_http_method = "POST"
  type        = "AWS_PROXY"
  uri         = aws_lambda_function.izettleminbal.invoke_arn
}

resource "aws_api_gateway_deployment" "izettleminbal_deployment" {
  rest_api_id = aws_api_gateway_rest_api.izettleminbal_api.id
  depends_on = [
    aws_api_gateway_integration.izettleminbal_integration
  ]
}

resource "aws_api_gateway_stage" "prod" {
  deployment_id = aws_api_gateway_deployment.izettleminbal_deployment.id
  rest_api_id   = aws_api_gateway_rest_api.izettleminbal_api.id
  stage_name    = "prod"

#  access_log_settings {
#    destination_arn = aws_cloudwatch_log_group.api_gateway_access_log.arn
#    format          = jsonencode({
#      requestId       = "$context.requestId"
#      ip              = "$context.identity.sourceIp"
#      caller          = "$context.identity.caller"
#      user            = "$context.identity.user"
#      requestTime     = "$context.requestTime"
#      httpMethod      = "$context.httpMethod"
#      resourcePath    = "$context.resourcePath"
#      status          = "$context.status"
#      protocol        = "$context.protocol"
#      responseLength  = "$context.responseLength"
#    })
#  }

#  variables = {
#    tracingEnabled = "true"
#    metricsEnabled = "true"
#  }
}

resource "aws_cloudwatch_log_group" "api_gateway_access_log" {
  name              = "/aws/apigateway/izettleminbal"
  retention_in_days = 7
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.izettleminbal.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.izettleminbal_api.execution_arn}/*/*"
}

output "api_url" {
  value = "https://${aws_api_gateway_rest_api.izettleminbal_api.id}.execute-api.${var.region}.amazonaws.com/prod/update_balance"
}