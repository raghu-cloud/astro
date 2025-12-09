docker buildx build --platform=linux/amd64 -t astro_backend -f Dockerfile .
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin 615299736283.dkr.ecr.ap-south-1.amazonaws.com
docker tag astro_backend:latest 615299736283.dkr.ecr.ap-south-1.amazonaws.com/astro:latest
docker push 615299736283.dkr.ecr.ap-south-1.amazonaws.com/astro:latest