terraform {
  backend "s3" {
    bucket = "kamoshika-terraform-agentcore-state-bucket"
    key    = "terraform_agentcore/terraform/terraform.tfstate"
    region = "ap-northeast-1"
  }
}
