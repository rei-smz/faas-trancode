# Prerequisites
- OpenFaaS
- Docker
- Minio DB
# Usage
1. Change the definition of OpenFaaS gateway and Minio DB in `stack.yml`.
2. Run `sudo env "PATH=$PATH" faas-cli up -f stack.yml`.
3. Upload your video to Minio DB.
4. Test your deployment.
