# 🚀 AWS App Runner Deployment Guide

> **Updated:** January 16, 2026 | Based on official AWS documentation

This project has been optimized for AWS App Runner deployment using Docker.

---

## ⚡ Quick Start

### Deploy in 3 Steps

```bash
# 1. Build Docker image
docker build -t astro-ai .

# 2. Push to ECR (first-time setup required - see below)
./deploy-to-apprunner.sh

# 3. Done! Your app is deploying ✅
```

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **[📖 Start Here: DEPLOYMENT_SUMMARY.md](./DEPLOYMENT_SUMMARY.md)** | Overview of changes and decisions |
| **[🚀 Quick Reference](./QUICK_DEPLOY_REFERENCE.md)** | Commands and troubleshooting |
| **[📘 Complete Guide](./AWS_APPRUNNER_SETUP.md)** | Detailed setup instructions |
| **[🏗️ Architecture](./ARCHITECTURE.md)** | System design and diagrams |
| **[🗂️ Index](./AWS_DEPLOYMENT_INDEX.md)** | All documentation links |

---

## ⚠️ Important

### ✅ Docker Deployment Required

This project **requires Docker-based deployment** because it uses:
- ✅ FFmpeg (audio processing)
- ✅ Playwright/Chromium (PDF generation)
- ✅ PostgreSQL client
- ✅ System libraries

❌ Source code deployment (managed runtime) is **NOT compatible**.

---

## 🔧 Configuration Files

### Updated
- ✅ `apprunner.yaml` - Fixed for source code deployment (reference only)
- ✅ `Dockerfile` - Ready for Docker deployment ⭐
- ✅ `deploy-to-apprunner.sh` - Automated deployment script

### Source Directory
✅ **Root directory (`/`)** - No configuration needed!

---

## 🎯 First-Time Setup

### 1. Create AWS Resources

```bash
# Set variables
export AWS_REGION="us-east-1"
export AWS_ACCOUNT_ID="YOUR_ACCOUNT_ID"

# Create ECR repository
aws ecr create-repository --repository-name astro-ai --region $AWS_REGION

# Create IAM role
aws iam create-role --role-name AppRunnerECRAccessRole \
  --assume-role-policy-document file://trust-policy.json

aws iam attach-role-policy \
  --role-name AppRunnerECRAccessRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess
```

### 2. Deploy

```bash
# Use automated script
./deploy-to-apprunner.sh
```

See **[QUICK_DEPLOY_REFERENCE.md](./QUICK_DEPLOY_REFERENCE.md)** for detailed commands.

---

## 📖 What Changed?

### apprunner.yaml Improvements
- ✅ Fixed runtime: `python311` (was `python3.11`)
- ✅ Added `runtime-version: 3.11`
- ✅ Added `pre-run` commands for migrations
- ✅ Updated to `pip3`/`python3` commands
- ✅ Improved Gunicorn configuration
- ⚠️ **Note:** Only use for reference; Docker deployment recommended

### New Documentation
- 📄 5 comprehensive guides created
- 🛠️ Automated deployment script
- 🏗️ Architecture diagrams
- 📋 Quick reference cheat sheet

### Critical Issue Fixed
- ⚠️ Identified system dependency incompatibility
- ✅ Provided Docker-based solution
- ✅ All features now fully supported

---

## 💰 Estimated Costs

- **App Runner:** ~$60-80/month (2 vCPU, 4GB)
- **RDS PostgreSQL:** ~$15-30/month
- **ECR Storage:** ~$1/month
- **Total:** ~$75-115/month

---

## 🆘 Need Help?

1. **Quick issues:** See [QUICK_DEPLOY_REFERENCE.md](./QUICK_DEPLOY_REFERENCE.md) → Troubleshooting
2. **Setup questions:** See [AWS_APPRUNNER_SETUP.md](./AWS_APPRUNNER_SETUP.md)
3. **System design:** See [ARCHITECTURE.md](./ARCHITECTURE.md)

---

## ✅ Checklist

### Before Deploying
- [ ] AWS account with admin access
- [ ] AWS CLI configured
- [ ] Docker installed
- [ ] Database ready (RDS/Neon/Supabase)
- [ ] Read [DEPLOYMENT_SUMMARY.md](./DEPLOYMENT_SUMMARY.md)

### Deploy
- [ ] Create ECR repository
- [ ] Create IAM roles
- [ ] Build Docker image
- [ ] Push to ECR
- [ ] Create App Runner service
- [ ] Configure secrets
- [ ] Test application

### After Deployment
- [ ] Set up monitoring
- [ ] Configure custom domain (optional)
- [ ] Set up CI/CD (optional)
- [ ] Monitor costs

---

## 🔗 Quick Links

- [App Runner Console](https://console.aws.amazon.com/apprunner)
- [ECR Console](https://console.aws.amazon.com/ecr)
- [CloudWatch Logs](https://console.aws.amazon.com/cloudwatch)
- [AWS Documentation](https://docs.aws.amazon.com/apprunner/latest/dg/config-file-examples.html)

---

## 📊 Status

✅ **Configuration:** Optimized and ready
✅ **Documentation:** Complete
✅ **Scripts:** Ready to use
🎯 **Action Required:** First-time AWS setup

---

**Ready to deploy?** → Start with **[DEPLOYMENT_SUMMARY.md](./DEPLOYMENT_SUMMARY.md)**









