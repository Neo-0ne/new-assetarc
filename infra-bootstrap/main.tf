
resource "aws_s3_bucket" "vault" {
  bucket = var.vault_bucket
  force_destroy = false
  versioning { enabled = true }
}

resource "aws_s3_bucket_lifecycle_configuration" "vault" {
  bucket = aws_s3_bucket.vault.id
  rule {
    id     = "expire-previews"
    status = "Enabled"
    filter { prefix = "previews/" }
    expiration { days = 60 }
  }
}

# (Optional) CloudFront can be added later to front S3 public assets.
