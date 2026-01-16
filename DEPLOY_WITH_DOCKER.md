# ⚠️ IMPORTANT: Use Docker Deployment

## Why Source Code Deployment Won't Work

Your `apprunner.yaml` is now syntactically correct, but your application **requires system dependencies** that are NOT available in App Runner managed runtimes:

- ❌ FFmpeg
- ❌ Chromium/Playwright
- ❌ PostgreSQL client
- ❌ System libraries

**Result:** Build may succeed, but application will crash at runtime when trying to use these features.

---

## ✅ Solution: Docker Deployment

Your `Dockerfile` already has all the necessary system dependencies configured!

### Quick Deploy (3 Commands)

```bash
# 1. Set your AWS account ID
export AWS_ACCOUNT_ID="YOUR_ACCOUNT_ID"
export AWS_REGION="us-east-1"

# 2. Create ECR repository (first time only)
aws ecr create-repository --repository-name astro-ai --region $AWS_REGION

# 3. Create IAM role (first time only)
aws iam create-role --role-name AppRunnerECRAccessRole \
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

# 4. Build and push
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

docker build -t astro-ai .
docker tag astro-ai:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/astro-ai:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/astro-ai:latest

# 5. Create App Runner service from Docker image
aws apprunner create-service \
  --service-name astro-ai-service \
  --source-configuration "{
    \"ImageRepository\": {
      \"ImageIdentifier\": \"$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/astro-ai:latest\",
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

### Or Use the Automated Script

```bash
./deploy-to-apprunner.sh
```

---

## 🎯 Next Steps

1. **Stop** trying to deploy with source code (apprunner.yaml)
2. **Delete** the current App Runner service if it was created
3. **Follow** the Docker deployment steps above
4. **Use** the automated script for future updates

---

## 📚 More Information

See these guides for detailed instructions:
- [QUICK_DEPLOY_REFERENCE.md](./QUICK_DEPLOY_REFERENCE.md)
- [AWS_APPRUNNER_SETUP.md](./AWS_APPRUNNER_SETUP.md)
- [DEPLOYMENT_SUMMARY.md](./DEPLOYMENT_SUMMARY.md)

---

**Summary:**
- ✅ `apprunner.yaml` is now syntactically correct
- ❌ But won't work for this project (missing system dependencies)
- ✅ Use Docker deployment instead (fully supported)

