# AWS App Runner Deployment Guide

This guide will help you deploy your AstroAI application to AWS App Runner.

## Deployment Options

You have **two options** for deploying to AWS App Runner:

### Option 1: Direct GitHub Deployment (Recommended)
AWS App Runner automatically builds and deploys from your GitHub repository.

### Option 2: GitHub Actions + ECR
Uses GitHub Actions to build Docker image and push to Amazon ECR, then deploy to App Runner.

---

## Option 1: Docker-Based Deployment (Recommended for this project)

**⚠️ Important:** This project requires system dependencies (ffmpeg, chromium/Playwright, PostgreSQL client) that are NOT available in App Runner managed runtimes. Therefore, Docker-based deployment is **REQUIRED**.

### Prerequisites
- AWS Account
- AWS CLI installed
- Docker installed locally
- GitHub repository with your code

### Step 1: Create ECR Repository
```bash
# Create ECR repository
aws ecr create-repository \
  --repository-name astro-ai \
  --region us-east-1

# Note the repository URI from output (e.g., 123456789012.dkr.ecr.us-east-1.amazonaws.com/astro-ai)
```

### Step 2: Build and Push Docker Image
```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Build your Docker image
docker build -t astro-ai .

# Tag the image
docker tag astro-ai:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/astro-ai:latest

# Push to ECR
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/astro-ai:latest
```

### Step 3: Create IAM Access Role
Create an IAM role that allows App Runner to access ECR:

```bash
# Create trust policy file
cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "build.apprunner.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create IAM role
aws iam create-role \
  --role-name AppRunnerECRAccessRole \
  --assume-role-policy-document file://trust-policy.json

# Attach ECR access policy
aws iam attach-role-policy \
  --role-name AppRunnerECRAccessRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess

# Note the role ARN from output
```

### Step 4: Create App Runner Service
```bash
aws apprunner create-service \
  --service-name astro-ai-service \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "123456789012.dkr.ecr.us-east-1.amazonaws.com/astro-ai:latest",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {
        "Port": "8000",
        "RuntimeEnvironmentVariables": {
          "PYTHONUNBUFFERED": "1",
          "DJANGO_SETTINGS_MODULE": "My_AI_Guruji.settings"
        }
      }
    },
    "AutoDeploymentsEnabled": false,
    "AuthenticationConfiguration": {
      "AccessRoleArn": "arn:aws:iam::123456789012:role/AppRunnerECRAccessRole"
    }
  }' \
  --instance-configuration '{
    "Cpu": "2 vCPU",
    "Memory": "4 GB"
  }' \
  --region us-east-1
```

---

## Option 2: Source Code Deployment (Limited - Not Recommended)

**⚠️ Warning:** Source code deployment uses managed Python runtime which does NOT support:
- System packages (ffmpeg, chromium, postgresql-client)
- Playwright browser automation
- Custom system libraries

Only use this if you remove all system dependencies from your application.

### Prerequisites
- AWS Account
- GitHub repository with your code
- AWS CLI installed (optional)

### Step 1: Push Code to GitHub
Ensure your code (with `apprunner.yaml`) is pushed to GitHub:
```bash
git add apprunner.yaml
git commit -m "Add App Runner configuration"
git push origin main
```

### Step 2: Create App Runner Service

#### Via AWS Console:
1. Go to [AWS App Runner Console](https://console.aws.amazon.com/apprunner)
2. Click **Create service**
3. **Source**: Select "Source code repository"
4. **Connect to GitHub**: 
   - Click "Add new" to connect your GitHub account
   - Select your repository
   - Select branch (main/master)
5. **Deployment settings**:
   - Deployment trigger: Automatic
   - Configuration file: Use configuration file (apprunner.yaml)
6. **Service settings**:
   - Service name: `astro-ai-service`
   - CPU: 2 vCPU
   - Memory: 4 GB
   - Port: 8000
7. **Environment variables**: Add these:
   ```
   DJANGO_SECRET_KEY=your-secret-key
   DATABASE_URL=your-database-url
   DEBUG=False
   ALLOWED_HOSTS=*.awsapprunner.com
   ```
8. Click **Create & deploy**

#### Via AWS CLI:
```bash
aws apprunner create-service \
  --service-name astro-ai-service \
  --source-configuration '{
    "CodeRepository": {
      "RepositoryUrl": "https://github.com/YOUR_USERNAME/YOUR_REPO",
      "SourceCodeVersion": {
        "Type": "BRANCH",
        "Value": "main"
      },
      "CodeConfiguration": {
        "ConfigurationSource": "API",
        "CodeConfigurationValues": {
          "Runtime": "PYTHON_3",
          "BuildCommand": "pip install -r requirements.txt",
          "StartCommand": "gunicorn --workers 2 --timeout 300 --bind 0.0.0.0:8000 My_AI_Guruji.wsgi:application",
          "Port": "8000",
          "RuntimeEnvironmentVariables": {
            "PYTHONUNBUFFERED": "1"
          }
        }
      }
    },
    "AutoDeploymentsEnabled": true
  }' \
  --instance-configuration '{
    "Cpu": "2 vCPU",
    "Memory": "4 GB"
  }' \
  --region us-east-1
```

---

## Option 3: Automated CI/CD with GitHub Actions + ECR

Automate your Docker builds and deployments using GitHub Actions.

### Prerequisites
- AWS Account with ECR enabled
- GitHub repository
- AWS Access Keys (for GitHub Actions)

### Step 1: Configure GitHub Secrets
In your GitHub repository, go to **Settings** → **Secrets and variables** → **Actions**, and add:

- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key
- `AWS_REGION`: `us-east-1` (or your preferred region)
- `ECR_REPOSITORY`: `astro-ai`
- `APP_RUNNER_SERVICE_ARN`: Your App Runner service ARN

### Step 2: Create GitHub Actions Workflow
Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to AWS App Runner

on:
  push:
    branches: [ main ]
  workflow_dispatch:

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: astro-ai
  
jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.AWS_REGION }}
    
    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1
    
    - name: Build, tag, and push image to Amazon ECR
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        IMAGE_TAG: ${{ github.sha }}
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
        docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
    
    - name: Deploy to App Runner
      run: |
        aws apprunner start-deployment --service-arn ${{ secrets.APP_RUNNER_SERVICE_ARN }}
```

### Step 3: Push to GitHub
The GitHub Actions workflow will automatically trigger on every push to main:

```bash
git add .github/workflows/deploy.yml
git commit -m "Add CI/CD workflow"
git push origin main
```

---

## Environment Variables

Add these environment variables in the App Runner service configuration:

### Required:
- `DJANGO_SECRET_KEY`: Your Django secret key
- `DATABASE_URL`: PostgreSQL connection string
- `ALLOWED_HOSTS`: Your App Runner domain

### Optional:
- `DEBUG`: Set to `False` for production
- `AWS_STORAGE_BUCKET_NAME`: If using S3 for media files
- `AWS_ACCESS_KEY_ID`: For S3 access
- `AWS_SECRET_ACCESS_KEY`: For S3 access
- `OPENAI_API_KEY`: For AI features
- `REDIS_URL`: For Celery/caching

---

## Source Repository Directory Configuration

**Q: Where do I configure the source repository directory?**

The source directory is configured when creating the App Runner service, NOT in `apprunner.yaml`.

### Your Project Structure:
```
/Users/raghunandanvenugopal/Documents/AstroAI/  ← Repository Root
├── apprunner.yaml          ← Configuration file
├── requirements.txt        ← Dependencies
├── manage.py              ← Django management
├── Dockerfile             ← Docker configuration
├── My_AI_Guruji/          ← Django project
├── langchain_agent/       ← Apps
└── ...
```

**✅ Your source directory is the root (`/`)** - No special configuration needed!

### When Creating Service:
- **Via AWS Console**: Leave "Source directory" field empty or enter `/`
- **Via AWS CLI**: Omit `SourceDirectory` or set to `/`

### If Using Docker (Option 1):
Source directory is irrelevant - Docker uses `WORKDIR` in Dockerfile.

---

## Using AWS Secrets Manager (Recommended)

Store sensitive data securely in AWS Secrets Manager:

### Step 1: Create Secrets
```bash
# Create a secret for your application
aws secretsmanager create-secret \
  --name astro-ai/prod \
  --description "Production secrets for AstroAI" \
  --secret-string '{
    "SECRET_KEY": "your-django-secret-key",
    "DB_NAME": "astro_db",
    "DB_USER": "postgres",
    "DB_PASSWORD": "your-db-password",
    "DB_HOST": "your-rds-endpoint.rds.amazonaws.com",
    "DB_PORT": "5432",
    "OPENAI_API_KEY": "sk-...",
    "CLERK_API_SECRET_KEY": "sk_live_..."
  }' \
  --region us-east-1

# Note the ARN from output (e.g., arn:aws:secretsmanager:us-east-1:123456789012:secret:astro-ai/prod-AbCdEf)
```

### Step 2A: For Docker-Based Deployment
Configure environment variables in App Runner service:

```bash
aws apprunner update-service \
  --service-arn YOUR_SERVICE_ARN \
  --source-configuration '{
    "ImageRepository": {
      "ImageConfiguration": {
        "RuntimeEnvironmentSecrets": {
          "SECRET_KEY": "arn:aws:secretsmanager:us-east-1:123456789012:secret:astro-ai/prod:SECRET_KEY::",
          "DB_PASSWORD": "arn:aws:secretsmanager:us-east-1:123456789012:secret:astro-ai/prod:DB_PASSWORD::",
          "OPENAI_API_KEY": "arn:aws:secretsmanager:us-east-1:123456789012:secret:astro-ai/prod:OPENAI_API_KEY::"
        }
      }
    }
  }'
```

### Step 2B: For Source Code Deployment (apprunner.yaml)
Update `apprunner.yaml`:

```yaml
run:
  secrets:
    # Secrets Manager format: arn:aws:secretsmanager:region:account:secret:name:json-key::
    - name: SECRET_KEY
      value-from: "arn:aws:secretsmanager:us-east-1:123456789012:secret:astro-ai/prod:SECRET_KEY::"
    - name: DB_PASSWORD
      value-from: "arn:aws:secretsmanager:us-east-1:123456789012:secret:astro-ai/prod:DB_PASSWORD::"
    
    # Systems Manager Parameter Store (simpler syntax)
    - name: SOME_CONFIG
      value-from: "parameter-name"  # SSM parameter (must exist)
```

### Step 3: Grant App Runner Access to Secrets
Create an IAM role with Secrets Manager access:

```bash
# Create instance role trust policy
cat > instance-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "tasks.apprunner.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create role
aws iam create-role \
  --role-name AppRunnerInstanceRole \
  --assume-role-policy-document file://instance-trust-policy.json

# Create and attach Secrets Manager policy
cat > secrets-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "ssm:GetParameters"
      ],
      "Resource": [
        "arn:aws:secretsmanager:us-east-1:123456789012:secret:astro-ai/*",
        "arn:aws:ssm:us-east-1:123456789012:parameter/*"
      ]
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name AppRunnerInstanceRole \
  --policy-name SecretsAccess \
  --policy-document file://secrets-policy.json
```

### Step 4: Update App Runner Service with Instance Role
```bash
aws apprunner update-service \
  --service-arn YOUR_SERVICE_ARN \
  --instance-configuration '{
    "InstanceRoleArn": "arn:aws:iam::123456789012:role/AppRunnerInstanceRole"
  }'
```

---

## Database Setup

### Option 1: Amazon RDS (Recommended)
```bash
aws rds create-db-instance \
  --db-instance-identifier astro-ai-db \
  --db-instance-class db.t4g.micro \
  --engine postgres \
  --master-username postgres \
  --master-user-password YOUR_PASSWORD \
  --allocated-storage 20 \
  --publicly-accessible \
  --region us-east-1
```

### Option 2: Supabase, Neon, or other managed PostgreSQL

Get the connection string and add it as `DATABASE_URL` environment variable.

---

## Monitoring & Logs

View logs in the App Runner console or via CLI:
```bash
aws apprunner list-operations --service-arn YOUR_SERVICE_ARN
aws logs tail /aws/apprunner/astro-ai-service --follow
```

---

## Scaling

App Runner auto-scales based on traffic. You can configure:
- **Min instances**: 1 (default)
- **Max instances**: 25 (default)
- **Max concurrency**: 100 requests per instance

---

## Cost Estimation

**Approximate monthly costs:**
- App Runner (2 vCPU, 4GB): ~$60-80/month (with auto-scaling)
- RDS db.t4g.micro: ~$15/month
- ECR storage: ~$1/month per GB

**Total**: ~$75-100/month for a small production deployment

---

## Troubleshooting

### Build fails
- Check build logs in App Runner console
- Verify `apprunner.yaml` syntax
- Ensure all dependencies are in `requirements.txt`

### Service won't start
- Check if port 8000 is exposed
- Verify `ALLOWED_HOSTS` includes App Runner domain
- Check database connectivity

### Playwright issues
- Increase memory to 4GB minimum
- Ensure system dependencies are installed in pre-build phase

---

## Next Steps

1. ✅ Push code with `apprunner.yaml` to GitHub
2. ✅ Create App Runner service (Option 1 or 2)
3. ✅ Configure environment variables
4. ✅ Set up database
5. ✅ Configure custom domain (optional)
6. ✅ Set up monitoring and alerts

## Useful Links

- [App Runner Documentation](https://docs.aws.amazon.com/apprunner/)
- [App Runner Pricing](https://aws.amazon.com/apprunner/pricing/)
- [GitHub Actions for AWS](https://github.com/aws-actions)


