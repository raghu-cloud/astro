# AWS App Runner Configuration Improvements

## ✅ Changes Made

### 1. **Fixed Runtime Specification**
- **Before**: `runtime: python3.11`
- **After**: `runtime: python311`
- **Reason**: AWS App Runner revised build uses runtime identifiers without dots (e.g., `python311`, `nodejs20`)

### 2. **Added Explicit Runtime Version**
```yaml
run:
  runtime-version: 3.11
```
This ensures the exact Python version is used.

### 3. **Added Pre-run Commands**
```yaml
run:
  pre-run:
    - python3 manage.py migrate --noinput
    - mkdir -p /tmp/notifications/logs
```
Pre-run commands execute before **each application start**, making them perfect for:
- Database migrations
- Health checks
- Runtime directory creation

### 4. **Improved Gunicorn Configuration**
```yaml
command: gunicorn --workers 2 --threads 4 --timeout 300 --bind 0.0.0.0:8000 --access-logfile - --error-logfile - My_AI_Guruji.wsgi:application
```
- Added `--threads 4` for better concurrency
- Added logging to stdout/stderr for CloudWatch integration
- Changed `APP_PORT` to `PORT` (AWS standard)

### 5. **Updated Build Commands**
- Changed `pip` to `pip3` and `python` to `python3` (required for Python 3.11)
- Removed migrations from post-build (moved to pre-run)
- Kept only `collectstatic` in post-build

## ⚠️ **CRITICAL ISSUES**

### Issue 1: System Dependencies Not Supported
Your configuration attempts to install system packages:
```yaml
- apt-get install -y ffmpeg libpq-dev gcc postgresql-client
- apt-get install -y chromium dependencies
- playwright install --with-deps chromium
```

**❌ This will NOT work in App Runner managed runtimes!**

AWS App Runner managed runtimes:
- Do NOT support `apt-get` or system package installation
- Do NOT include ffmpeg, chromium, or other system tools
- Have a read-only filesystem except for `/tmp`

### Issue 2: Playwright Compatibility
Playwright requires:
- System dependencies (chromium browser)
- Write access to filesystem
- Large memory footprint

**This is NOT compatible with App Runner managed runtimes.**

## 🔧 **SOLUTIONS**

### Option 1: Switch to Docker-Based Deployment (RECOMMENDED)

**Pros:**
- Full control over system dependencies
- Can install ffmpeg, chromium, etc.
- Works with Playwright
- More flexible

**Steps:**
1. Use your existing `Dockerfile` instead of `apprunner.yaml`
2. Push Docker image to Amazon ECR
3. Deploy App Runner service from ECR image

**Update your deployment:**
```bash
# Build and push Docker image
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ECR_REGISTRY
docker build -t astro-ai .
docker tag astro-ai:latest YOUR_ECR_REGISTRY/astro-ai:latest
docker push YOUR_ECR_REGISTRY/astro-ai:latest

# Create App Runner service from ECR
aws apprunner create-service \
  --service-name astro-ai-service \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "YOUR_ECR_REGISTRY/astro-ai:latest",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {
        "Port": "8000"
      }
    },
    "AutoDeploymentsEnabled": true
  }' \
  --instance-configuration '{
    "Cpu": "2 vCPU",
    "Memory": "4 GB"
  }'
```

### Option 2: Remove System Dependencies (Simpler)

If you can work without:
- Playwright/Chromium
- FFmpeg
- System-level audio processing

Then the current `apprunner.yaml` configuration will work fine.

**Update your code to:**
- Use cloud services for PDF generation instead of Playwright
- Use external APIs for audio processing
- Remove system dependency requirements

### Option 3: Hybrid Approach

Keep App Runner for your Django app, but:
- Use AWS Lambda for Playwright/PDF generation tasks
- Use external services (e.g., Deepgram API) for audio processing
- Keep only Python dependencies in App Runner

## 📁 **Source Repository Directory**

**Q: What about source repository directory?**

The source directory is **NOT** configured in `apprunner.yaml`. It's configured when creating the App Runner service:

### Via AWS Console:
1. When creating service → **Source code** section
2. **Source directory**: Leave empty if code is in root (your case ✅)
3. If your code was in a subdirectory like `backend/`, you'd specify: `backend`

### Via AWS CLI:
```bash
aws apprunner create-service \
  --source-configuration '{
    "CodeRepository": {
      "RepositoryUrl": "https://github.com/user/repo",
      "SourceCodeVersion": {"Type": "BRANCH", "Value": "main"},
      "SourceDirectory": "/",  # Root directory
      "CodeConfiguration": {
        "ConfigurationSource": "REPOSITORY"  # Uses apprunner.yaml
      }
    }
  }'
```

**Your project structure:**
```
/Users/raghunandanvenugopal/Documents/AstroAI/  ← Root (✅ Source directory is "/")
├── apprunner.yaml
├── requirements.txt
├── manage.py
├── My_AI_Guruji/
└── ... other files
```

Since your `manage.py`, `requirements.txt`, and `apprunner.yaml` are all in the root, you should use:
- **Source directory**: `/` or leave empty

## 🎯 **Recommended Next Steps**

1. **Decision Time**: Choose between:
   - **Docker-based deployment** (if you need system dependencies)
   - **Managed runtime** (if you can remove system dependencies)

2. **If using Docker:**
   - Check your `Dockerfile`
   - Set up ECR repository
   - Update deployment to use ECR instead of source code

3. **If using Managed Runtime (current apprunner.yaml):**
   - Remove Playwright, ffmpeg dependencies
   - Test without system-level features
   - Deploy with updated configuration

4. **Configure Secrets:**
   - Store sensitive data in AWS Secrets Manager
   - Update `apprunner.yaml` secrets section with actual ARNs

5. **Test Deployment:**
   ```bash
   git add apprunner.yaml
   git commit -m "Update App Runner configuration"
   git push origin main
   ```

## 📚 **References**

- [App Runner Configuration File Examples](https://docs.aws.amazon.com/apprunner/latest/dg/config-file-examples.html)
- [Python Runtime Guide](https://docs.aws.amazon.com/apprunner/latest/dg/service-source-code-python.html)
- [Docker-based Services](https://docs.aws.amazon.com/apprunner/latest/dg/service-source-image.html)
- [Revised vs Original Build](https://docs.aws.amazon.com/apprunner/latest/dg/service-source-code.html#service-source-code-build-versions)

---

## Summary

✅ **Improved**: Runtime configuration, pre-run commands, gunicorn settings
⚠️ **Critical**: System dependencies won't work with managed runtime
🔧 **Solution**: Switch to Docker-based deployment OR remove system dependencies
📁 **Source Directory**: Root directory ("/") - already correct for your setup









