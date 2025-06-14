# Description: Terraform module for Lambda API Ingestor.
# Source: Cloud Migration + Terraform Snippets Deep-Dive Addendum, Section 9.2.
#
# This module provisions AWS resources for a FastAPI Lambda API ingestor.
# It includes ECR repository, IAM role with necessary policies (basic execution, VPC, MSK publish),
# and the Lambda function itself.
resource "aws_ecr_repository" "fastapi_repo" {
  name = "${var.project_name}/fastapi-ingestor"
  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM Role for Lambda function
resource "aws_iam_role" "lambda_exec_role" {
  name = "${var.project_name}-lambda-fastapi-exec-role-${var.environment}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_iam_role_policy_attachment" "lambda_basic_exec" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_vpc_access" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# Policy to allow Lambda to publish to MSK (example)
resource "aws_iam_policy" "lambda_msk_publish" {
  name        = "${var.project_name}-lambda-msk-publish-policy-${var.environment}"
  description = "Allows Lambda function to produce messages to MSK topic"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = [
        "kafka-action:DescribeCluster",
        "kafka-action:GetBootstrapBrokers",
        "kafka-action:GetTopicPartitions",
        "kafka-action:ListTopics",
        "kafka-action:Produce"
      ]
      Effect   = "Allow"
      Resource = var.msk_cluster_arn # This ARN should be passed as a variable
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_msk_publish_attach" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.lambda_msk_publish.arn
}

resource "aws_lambda_function" "fastapi_ingestor_lambda" {
  function_name = "${var.project_name}-fastapi-ingestor-${var.environment}"
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.fastapi_repo.repository_url}:${var.fastapi_image_tag}"
  role          = aws_iam_role.lambda_exec_role.arn
  timeout       = 30 # seconds
  memory_size   = 512 # MB

  vpc_config {
    subnet_ids         = var.subnet_ids
    security_group_ids = [var.security_group_id]
  }

  environment {
    variables = {
      KAFKA_BROKER_ADDRESSES = var.msk_bootstrap_brokers_tls # From MSK output
      KAFKA_TOPIC_FINANCIAL  = var.kafka_topic_name_financial
      KAFKA_TOPIC_INSURANCE  = var.kafka_topic_name_insurance
      # ... other FastAPI env vars needed for cloud deployment
    }
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}