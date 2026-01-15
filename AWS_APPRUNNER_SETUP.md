# AWS App Runner Deployment Guide

This guide will help you deploy your AstroAI application to AWS App Runner.

## Deployment Options

You have **two options** for deploying to AWS App Runner:

### Option 1: Direct GitHub Deployment (Recommended)
AWS App Runner automatically builds and deploys from your GitHub repository.

### Option 2: GitHub Actions + ECR
Uses GitHub Actions to build Docker image and push to Amazon ECR, then deploy to App Runner.

---

## Option 1: Direct GitHub Deployment

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

## Option 2: GitHub Actions + ECR Deployment

### Prerequisites
- AWS Account with ECR enabled
- GitHub repository
- AWS Access Keys

### Step 1: Create ECR Repository
```bash
aws ecr create-repository \
  --repository-name astro-ai \
  --region us-east-1
```

### Step 2: Create IAM Role for App Runner
Create an IAM role with the following trust policy:
```json
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
```

Attach the policy `AWSAppRunnerServicePolicyForECRAccess`

### Step 3: Configure GitHub Secrets
In your GitHub repository, go to **Settings** → **Secrets and variables** → **Actions**, and add:

- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key
- `APP_RUNNER_ACCESS_ROLE_ARN`: The ARN of the IAM role created above

### Step 4: Push to GitHub
The GitHub Actions workflow will automatically:
1. Build your Docker image
2. Push to ECR
3. Deploy to App Runner

```bash
git add .github/workflows/deploy-apprunner.yml
git commit -m "Add GitHub Actions workflow"
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

## Using AWS Secrets Manager (Recommended)

Store sensitive data in AWS Secrets Manager:

```bash
# Create secret
aws secretsmanager create-secret \
  --name astro-ai/prod \
  --secret-string '{
    "DJANGO_SECRET_KEY": "your-secret-key",
    "DATABASE_URL": "postgresql://...",
    "OPENAI_API_KEY": "sk-..."
  }' \
  --region us-east-1
```

Update `apprunner.yaml` to reference secrets:
```yaml
run:
  env:
    - name: DJANGO_SECRET_KEY
      value-from: "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:astro-ai/prod:DJANGO_SECRET_KEY::"
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

