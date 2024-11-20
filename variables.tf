variable "log_expiration_days" {
  description = "Number of days after which logs are deleted"
  type        = number
  default     = 7
}

variable "screenshot_expiration_days" {
  description = "Number of days after which screenshots are deleted"
  type        = number
  default     = 7
}

variable "region" {
  description = "The AWS region to deploy resources"
  type        = string
  default     = "eu-west-2"
}