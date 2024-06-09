terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Configure the AWS Provider
provider "aws" {
  region = "ap-southeast-1"
}

# resource "aws_s3_bucket" "tf_s3" {
#   bucket = "yt-slowed-s3" 
#   force_destroy = true
# }

# resource "aws_s3_bucket_versioning" "terraform_bucket_versioning" {
#   bucket = aws_s3_bucket.terraform_state.id
#   versioning_configuration {
#     status = "Enabled"
#   }
# }

# resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state_crypto_conf" {
#   bucket = aws_s3_bucket.terraform_state.bucket 
#   rule {
#     apply_server_side_encryption_by_default {
#       sse_algorithm = "AES256"
#     }
#   }
# }


resource "aws_instance" "instance_1" {
ami             = "ami-003c463c8207b4dfa" 
instance_type   = "t2.micro"
security_groups = [aws_security_group.my_sg.id]
user_data       = <<-EOF
            #!/bin/bash
            echo "Hello, World 1" > index.html
            python3 -m http.server 8080 &
            EOF
}


resource "aws_security_group" "my_sg" {
    name        = "my_sg"
    description = "Some description"

    ingress {
        from_port   = "80"
        to_port     = "80"
        protocol    = "TCP"
        cidr_blocks = ["0.0.0.0/0"]
    }

    egress {
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }
}