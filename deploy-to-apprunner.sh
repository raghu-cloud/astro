#!/bin/bash

# AWS App Runner Deployment Script for AstroAI
# This script automates the Docker build and deployment process

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
ECR_REPO="${ECR_REPO:-astro-ai}"
SERVICE_NAME="${SERVICE_NAME:-astro-ai-service}"

# Functions
print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Get AWS Account ID
get_aws_account_id() {
    aws sts get-caller-identity --query Account --output text 2>/dev/null
}

# Check if service exists
service_exists() {
    aws apprunner list-services --region "$AWS_REGION" 2>/dev/null | \
        grep -q "\"ServiceName\": \"$SERVICE_NAME\""
}

# Main script
main() {
    print_header "AWS App Runner Deployment Script"
    
    # Check prerequisites
    print_info "Checking prerequisites..."
    
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    print_success "AWS CLI found"
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install it first."
        exit 1
    fi
    print_success "Docker found"
    
    # Get AWS Account ID
    print_info "Getting AWS Account ID..."
    AWS_ACCOUNT_ID=$(get_aws_account_id)
    if [ -z "$AWS_ACCOUNT_ID" ]; then
        print_error "Failed to get AWS Account ID. Check your AWS credentials."
        exit 1
    fi
    print_success "AWS Account ID: $AWS_ACCOUNT_ID"
    
    # Set ECR URI
    ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO"
    
    # Check if this is first-time setup
    if ! service_exists; then
        print_warning "Service '$SERVICE_NAME' does not exist."
        print_info "This appears to be first-time setup."
        print_info "Please run the following commands first:"
        echo ""
        echo "1. Create ECR repository:"
        echo "   aws ecr create-repository --repository-name $ECR_REPO --region $AWS_REGION"
        echo ""
        echo "2. Create IAM role for ECR access:"
        echo "   aws iam create-role --role-name AppRunnerECRAccessRole --assume-role-policy-document file://trust-policy.json"
        echo "   aws iam attach-role-policy --role-name AppRunnerECRAccessRole --policy-arn arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
        echo ""
        echo "3. Create App Runner service (see QUICK_DEPLOY_REFERENCE.md)"
        echo ""
        print_info "After setup, run this script again to deploy updates."
        exit 0
    fi
    
    # Docker build
    print_header "Building Docker Image"
    print_info "Building image: $ECR_REPO"
    if docker build -t "$ECR_REPO" .; then
        print_success "Docker image built successfully"
    else
        print_error "Docker build failed"
        exit 1
    fi
    
    # ECR login
    print_header "Logging into Amazon ECR"
    if aws ecr get-login-password --region "$AWS_REGION" | \
        docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"; then
        print_success "Logged into ECR"
    else
        print_error "ECR login failed"
        exit 1
    fi
    
    # Tag image
    print_header "Tagging Docker Image"
    print_info "Tagging as: $ECR_URI:latest"
    if docker tag "$ECR_REPO:latest" "$ECR_URI:latest"; then
        print_success "Image tagged successfully"
    else
        print_error "Image tagging failed"
        exit 1
    fi
    
    # Push to ECR
    print_header "Pushing to Amazon ECR"
    print_info "Pushing to: $ECR_URI:latest"
    if docker push "$ECR_URI:latest"; then
        print_success "Image pushed successfully"
    else
        print_error "Image push failed"
        exit 1
    fi
    
    # Get service ARN
    print_header "Deploying to App Runner"
    print_info "Getting service ARN..."
    SERVICE_ARN=$(aws apprunner list-services --region "$AWS_REGION" --query \
        "ServiceSummaryList[?ServiceName=='$SERVICE_NAME'].ServiceArn" --output text)
    
    if [ -z "$SERVICE_ARN" ]; then
        print_error "Could not find service: $SERVICE_NAME"
        exit 1
    fi
    print_success "Service ARN: $SERVICE_ARN"
    
    # Trigger deployment
    print_info "Starting deployment..."
    if aws apprunner start-deployment \
        --service-arn "$SERVICE_ARN" \
        --region "$AWS_REGION" > /dev/null; then
        print_success "Deployment started!"
    else
        print_error "Failed to start deployment"
        exit 1
    fi
    
    # Success message
    print_header "Deployment Complete!"
    echo ""
    print_success "Docker image pushed to ECR"
    print_success "App Runner deployment initiated"
    echo ""
    print_info "Monitor deployment status:"
    echo "  aws apprunner describe-service --service-arn $SERVICE_ARN"
    echo ""
    print_info "View logs:"
    echo "  aws logs tail /aws/apprunner/$SERVICE_NAME --follow"
    echo ""
    print_info "Service URL will be available in AWS Console:"
    echo "  https://console.aws.amazon.com/apprunner"
    echo ""
}

# Run main function
main "$@"

