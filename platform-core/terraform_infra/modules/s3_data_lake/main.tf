# terraform_infra/modules/s3_data_lake/main.tf
# This Terraform module defines S3 buckets for raw and curated data zones.
# In a real cloud migration, these would replace your local MinIO setup.
# It includes server-side encryption as a best practice.

resource "aws_s3_bucket" "raw_data_bucket" {
  # Naming convention for the raw data bucket
  bucket = "${var.project_name}-raw-${var.environment}-${var.aws_region}"

  tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "raw_data_bucket_encryption" {
  # Apply default server-side encryption (SSE-S3) to the raw data bucket
  bucket = aws_s3_bucket.raw_data_bucket.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket" "curated_data_bucket" {
  # Naming convention for the curated data bucket
  bucket = "${var.project_name}-curated-${var.environment}-${var.aws_region}"

  tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "curated_data_bucket_encryption" {
  # Apply default server-side encryption (SSE-S3) to the curated data bucket
  bucket = aws_s3_bucket.curated_data_bucket.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Output the ARNs (Amazon Resource Names) of the created buckets.
# These outputs can be referenced by other Terraform modules or CI/CD pipelines.
output "raw_bucket_arn" {
  value = aws_s3_bucket.raw_data_bucket.arn
  description = "The ARN of the raw data S3 bucket."
}

output "curated_bucket_arn" {
  value = aws_s3_bucket.curated_data_bucket.arn
  description = "The ARN of the curated data S3 bucket."
}

# Example of variables that would be defined in variables.tf for this module:
/*
variable "project_name" {
  description = "Name of the project (e.g., data-platform)"
  type        = string
}

variable "environment" {
  description = "Deployment environment (e.g., dev, staging, prod)"
  type        = string
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
}
*/
