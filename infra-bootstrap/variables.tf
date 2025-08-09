
variable "region" { type = string, default = "af-south-1" }
variable "vault_bucket" { type = string, default = "assetarc-vault" }
variable "ses_identity" { type = string, description = "Sender domain for SES (eu-west-1)", default = "asset-arc.com" }
