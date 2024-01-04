resource "aws_s3_bucket" "iceman_s3_bucket" {
  bucket = "iceman-lambda-functions"
  tags = {
    Name        = "Iceman Lambda Functions"
    Environment = var.environment
  }
}

resource "aws_s3_bucket" "iceman_identitycenterreports" {
  bucket = "iceman-identitycenterreports"
}

resource "aws_s3_bucket" "iceman_tfstate_dev" {
  bucket = "iceman-tfstate-dev"
}

resource "aws_s3_bucket_versioning" "tfstate_versioning" {
  bucket = aws_s3_bucket.iceman_tfstate_dev.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_versioning" "identitystorereports_versioning" {
  bucket = aws_s3_bucket.iceman_identitycenterreports.id
  versioning_configuration {
    status = "Enabled"
  }
}


resource "aws_s3_bucket_public_access_block" "iceman_s3_bucket_public_access_block" {
  bucket = aws_s3_bucket.iceman_s3_bucket.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
