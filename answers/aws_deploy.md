# AWS deployment approach (extra credit)

- **API**: Containerize FastAPI, push to ECR, deploy on ECS Fargate behind an ALB.
- **Database**: RDS Postgres (multi-AZ) with security groups limiting access to ECS tasks.
- **Ingestion**: ECS scheduled task or AWS Lambda triggered by EventBridge to load raw data on a schedule.
- **Storage**: S3 for raw weather/yield files and ingestion checkpoints.
- **Migrations**: Alembic run as a one-off ECS task in CI/CD.
- **Secrets/config**: AWS Secrets Manager + SSM Parameter Store.
- **Observability**: CloudWatch logs/metrics, alarms, and ALB access logs in S3.
- **CI/CD**: GitHub Actions to build/push images and update ECS service.
