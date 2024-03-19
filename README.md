# Prerequisites
- OpenFaaS
- Docker
- Minio DB
# Usage
1. Change the definition of OpenFaaS gateway and Minio DB in `stack.yml`.
2. Create secrets: 

```bash
sudo env "PATH=$PATH" faas-cli secret create minio-access-key --from-literal=your_minio_access_key
sudo env "PATH=$PATH" faas-cli secret create minio-secret-key --from-literal=your_minio_secret_key
```

1. Run `sudo env "PATH=$PATH" faas-cli up -f stack.yml`.
2. Upload your video to Minio DB.
3. Test your deployment.
