
# AssetArc – Infra Bootstrap (Terraform)

Minimal Terraform to provision:
- S3 bucket (Vault) in af-south-1 with versioning
- Public CloudFront distribution for static assets (optional)
- IAM user with policy for S3 + SES send email

> Run: terraform init && terraform apply (after filling variables).

