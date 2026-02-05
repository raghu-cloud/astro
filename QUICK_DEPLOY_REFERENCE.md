# Quick Deploy Reference - AWS App Runner

## 🎯 Which Deployment Method Should I Use?

### ✅ Use Docker-Based Deployment (Option 1)
**Required for this project** because you need:
- ✅ ffmpeg (audio processing)
- ✅ Chromium/Playwright (PDF generation)
- ✅ PostgreSQL client
- ✅ System libraries (libgl1, libglib2.0-0, etc.)

### ❌ Don't Use Source Code Deployment (Option 2)
**Not compatible** with this project due to system dependencies.

---

## 🚀 Quick Deploy Steps (Docker-Based)

### 1️⃣ One-Time Setup

```bash
# Set your AWS region and account ID
export AWS_REGION="us-east-1"
export AWS_ACCOUNT_ID="123456789012"  # Replace with your account ID
export ECR_REPO="astro-ai"

# Create ECR repository
aws ecr create-repository --repository-name $ECR_REPO --region $AWS_REGION

# Create IAM role for ECR access
aws iam create-role \
  --role-name AppRunnerECRAccessRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "build.apprunner.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

aws iam attach-role-policy \
  --role-name AppRunnerECRAccessRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess
```

### 2️⃣ Build & Push Docker Image

```bash
# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build image
docker build -t $ECR_REPO .

# Tag and push
docker tag $ECR_REPO:latest \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest

docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest
```

### 3️⃣ Create App Runner Service

```bash
aws apprunner create-service \
  --service-name astro-ai-service \
  --source-configuration "{
    \"ImageRepository\": {
      \"ImageIdentifier\": \"$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest\",
      \"ImageRepositoryType\": \"ECR\",
      \"ImageConfiguration\": {
        \"Port\": \"8000\",
        \"RuntimeEnvironmentVariables\": {
          \"PYTHONUNBUFFERED\": \"1\",
          \"DJANGO_SETTINGS_MODULE\": \"My_AI_Guruji.settings\"
        }
      }
    },
    \"AutoDeploymentsEnabled\": false,
    \"AuthenticationConfiguration\": {
      \"AccessRoleArn\": \"arn:aws:iam::$AWS_ACCOUNT_ID:role/AppRunnerECRAccessRole\"
    }
  }" \
  --instance-configuration '{
    "Cpu": "2 vCPU",
    "Memory": "4 GB"
  }' \
  --region $AWS_REGION
```

### 4️⃣ Update on Code Changes

```bash
# Rebuild and push
docker build -t $ECR_REPO .
docker tag $ECR_REPO:latest \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest

# Trigger deployment
aws apprunner start-deployment --service-arn YOUR_SERVICE_ARN
```

---

## 🔐 Environment Variables & Secrets

### Add Environment Variables
```bash
# Update service with env vars
aws apprunner update-service \
  --service-arn YOUR_SERVICE_ARN \
  --source-configuration '{
    "ImageRepository": {
      "ImageConfiguration": {
        "RuntimeEnvironmentVariables": {
          "DEBUG": "False",
          "ALLOWED_HOSTS": "*.awsapprunner.com",
          "DB_HOST": "your-db-host.rds.amazonaws.com",
          "DB_NAME": "astro_db",
          "DB_USER": "postgres",
          "DB_PORT": "5432"
        }
      }
    }
  }'
```

### Add Secrets (Recommended)
```bash
# Create secret in Secrets Manager
aws secretsmanager create-secret \
  --name astro-ai/prod \
  --secret-string '{
    "SECRET_KEY": "your-django-secret",
    "DB_PASSWORD": "your-db-password",
    "OPENAI_API_KEY": "sk-..."
  }'

# Update service with secrets
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

---

## 📊 Useful Commands

### Get Service Status
```bash
aws apprunner list-services --region $AWS_REGION
aws apprunner describe-service --service-arn YOUR_SERVICE_ARN
```

### View Logs
```bash
# Get service ID from ARN
aws logs tail /aws/apprunner/astro-ai-service --follow
```

### Update Service Configuration
```bash
# Scale up/down
aws apprunner update-service \
  --service-arn YOUR_SERVICE_ARN \
  --instance-configuration '{
    "Cpu": "4 vCPU",
    "Memory": "8 GB"
  }'
```

### Delete Service
```bash
aws apprunner delete-service --service-arn YOUR_SERVICE_ARN
```

---

## ✅ Checklist

### Before First Deployment:
- [ ] Create ECR repository
- [ ] Create IAM role (AppRunnerECRAccessRole)
- [ ] Set up database (RDS PostgreSQL)
- [ ] Create secrets in Secrets Manager
- [ ] Update ALLOWED_HOSTS in Django settings

### For Each Deployment:
- [ ] Build Docker image locally
- [ ] Tag and push to ECR
- [ ] Start App Runner deployment
- [ ] Verify service health
- [ ] Test application endpoint

### After Deployment:
- [ ] Run database migrations (if needed)
- [ ] Test key features (TTS, STT, PDF generation)
- [ ] Monitor logs for errors
- [ ] Set up custom domain (optional)

---

## 🐛 Troubleshooting

### Build Fails
```bash
# Test locally first
docker build -t astro-ai .
docker run -p 8000:8000 astro-ai
```

### Service Won't Start
- Check environment variables
- Verify ALLOWED_HOSTS includes App Runner domain
- Check database connectivity
- Review CloudWatch logs

### Out of Memory
- Increase memory to 4GB or 8GB
- Reduce Gunicorn workers
- Optimize Playwright/Chrome usage

### Permission Errors
- Verify IAM roles are attached
- Check Secrets Manager permissions
- Ensure ECR authentication is valid

---

## 📌 Important Notes

1. **Source Directory**: Root (`/`) - already correct ✅
2. **System Dependencies**: Use Docker, not managed runtime ✅
3. **Port**: Must be 8000 (matches Dockerfile) ✅
4. **Secrets**: Use Secrets Manager, not environment variables ✅
5. **Auto-deploy**: Set to `false` for manual control ✅

---

## 💰 Estimated Costs

- **App Runner**: ~$60-80/month (2 vCPU, 4GB RAM)
- **RDS PostgreSQL**: ~$15-30/month (db.t4g.micro)
- **ECR Storage**: ~$1/month per GB
- **Data Transfer**: Variable based on usage
- **Secrets Manager**: $0.40/secret/month + API calls

**Total**: ~$75-115/month for small-scale production

---

## 🔗 Quick Links

- [App Runner Console](https://console.aws.amazon.com/apprunner)
- [ECR Console](https://console.aws.amazon.com/ecr)
- [Secrets Manager Console](https://console.aws.amazon.com/secretsmanager)
- [CloudWatch Logs](https://console.aws.amazon.com/cloudwatch)









