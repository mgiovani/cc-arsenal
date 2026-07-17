# Service Catalog

Load this when Phase 2 needs to map a detected dependency to a service, or
Phase 3 needs the health check command for a service not already shown inline
in SKILL.md.

## Dependency-to-service mapping

| Detected | Proposed Service | Default Image |
|----------|-----------------|---------------|
| `pg`, `psycopg`, `postgres` | PostgreSQL | `postgres:16-alpine` |
| `mysql`, `pymysql` | MySQL | `mysql:8.0` |
| `redis`, `ioredis` | Redis / Valkey | `redis:7-alpine` |
| `mongodb`, `pymongo` | MongoDB | `mongo:7` |
| `rabbitmq`, `pika`, `amqp` | RabbitMQ | `rabbitmq:3-management-alpine` |
| `kafka`, `confluent`, `kafkajs` | Kafka (KRaft, single node) | `apache/kafka:latest` — pin to a specific tag (e.g. `3.8.0`) before deploying to prod |
| `meilisearch` | Meilisearch | `getmeili/meilisearch:v1.9` |
| `elasticsearch` | Elasticsearch | `elasticsearch:8.15.0` — check https://www.elastic.co/downloads/elasticsearch for a newer 8.x patch before deploying |
| `celery`, `sidekiq` | Redis (queue backend) | `redis:7-alpine` |
| `mailhog`, `smtp`, `mailer` | Mailhog | `mailhog/mailhog:v1.0.1` |
| `minio`, `s3` | MinIO | `minio/minio:latest` — pin to a specific `RELEASE.*` tag before deploying to prod |

MinIO and Elasticsearch don't publish clean floating major-version tags the
way Postgres/Redis/Mongo do, so their default is either `latest` or a patch
pin — always accompanied by the pin/check comment shown above so it doesn't
rot silently in a generated file.

## Health check patterns per service

| Service | Health Check |
|---------|-------------|
| Postgres | `pg_isready -U ${USER}` |
| MySQL | `mysqladmin ping -h localhost` |
| Redis | `redis-cli ping` |
| MongoDB | `mongosh --eval "db.adminCommand('ping')"` |
| RabbitMQ | `rabbitmq-diagnostics -q ping` |
| Kafka (KRaft) | `kafka-broker-api-versions.sh --bootstrap-server localhost:9092` |
| MinIO | `mc ready local` |
