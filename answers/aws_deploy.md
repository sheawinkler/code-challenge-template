# AWS deployment approach (extra credit)

Here’s the simple, production‑ish setup I’d use:

- **API**: Containerize FastAPI, push to AWS container registery (ECR), deploy on container service (ECS Fargate - containers w/o resource management) utilizing elastic load balancing (most flexible for varied job size), or deploy as an app on an EC2 (/EC2 Spot) instance for tighter resource controls (batch processing to manage ingestion size, more infra to manage, potentially cheaper).
- **Database**: RDS Postgres with security groups limiting access to ECS tasks (minimum: api consumers vs engineers). Consider utilizing Multi-AZ (cross-region replicas) deployment for failover depending on required uptime for dataset
- **Ingestion**: options: ECS scheduled task, or schedule as cron via Kubernetes/kustomizations if that infra is used at Corteva, or could use AWS Lambda triggered by EventBridge to load raw data on a schedule.
- **Storage**: S3 for raw weather/yield files and ingestion checkpoints. RDS for postgres tables. And/or ingestion to Databricks.
- **Migrations**: Alembic run as a one‑off ECS task in CI/CD to track SQLite or PostgreSQL histories. Alembic is not reliable with Databricks so added example code/stubs for what Databricks migrations should look like.
- **Secrets/config**: AWS Secrets Manager + SSM Parameter Store for setting env vars (especially if not done in k8s).
- **Observability**: CloudWatch logs/metrics, alarms, and Application Load Balancer (ALB) access logs in S3.
- **CI/CD**: GitHub Actions to build/push images to ECR and update ECS service (dev vs. prod domains).
