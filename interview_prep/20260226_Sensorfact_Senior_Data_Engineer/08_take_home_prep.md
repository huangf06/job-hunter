# Take-Home Assignment Prep — Sensorfact

## GitHub Intelligence (CRITICAL)

Sensorfact's GitHub organization [Sensorfactdev](https://github.com/Sensorfactdev) has **16 public repos** including **4+ take-home assignments**.

### Public Assignments Found

| Assignment | Role | Language | Time | Link |
|-----------|------|----------|------|------|
| **backend-assignment-btcenergy** | Backend Dev | TypeScript | ~4 hrs | [Repo](https://github.com/Sensorfactdev/backend-assignment-btcenergy) |
| **backend-integration-assignment** | Backend Integration | TypeScript | ~4 hrs | [Repo](https://github.com/Sensorfactdev/backend-integration-assignment) |
| **iot-python-assignment** | IoT Engineer | Python 3.7 | ~6 hrs | [Repo](https://github.com/Sensorfactdev/iot-python-assignment) |
| **frontend-assignment-spacex** | Frontend Dev | React/TS | ~4-5 hrs | [Repo](https://github.com/Sensorfactdev/frontend-assignment-spacex) |
| **sw-case** | Full-stack Junior | Node.js/React | N/A | [Repo](https://github.com/Sensorfactdev/sw-case) |

**No public Data Engineer assignment** — it's likely shared privately. But the patterns are clear.

### Pattern Analysis — What to Expect

1. **Energy/sensor data theme**: Every assignment involves energy calculations (Bitcoin energy per transaction, SpaceX launch energy, sensor readings). Expect **sensor data processing**.
2. **GraphQL is central**: 3/4 assignments require a GraphQL API. Expect GraphQL involvement even in DE.
3. **Time-boxed 4-6 hours**: Incomplete solutions accepted if prioritization is conscious.
4. **Evaluation criteria**: Architecture decisions, library choices, code maintainability, scalability, trade-off discussion.
5. **AI tools explicitly allowed** — but decisions must be defensible.

### Predicted Data Engineer Assignment

Based on patterns + their actual stack:
- **Domain**: Sensor data processing (energy consumption metrics)
- **Tech**: Python, possibly Kafka/ClickHouse/Flink concepts
- **Task**: Likely build a data pipeline processing sensor readings → aggregation → exposure
- **Bonus**: GraphQL API exposure, data quality handling
- **Format**: ~4-6 hours, emphasis on trade-offs over completeness

## Internal Tools Revealed by GitHub

| Repo | Reveals | Link |
|------|---------|------|
| **mock-node-nats** | They use **NATS** messaging for microservices | [Repo](https://github.com/Sensorfactdev/mock-node-nats) |
| **draconarius** | Custom **feature flag** system | [Repo](https://github.com/Sensorfactdev/draconarius) |
| **i18n** | i18n backed by **GraphQL translations** | [Repo](https://github.com/Sensorfactdev/i18n) |
| **graphql-schema-builder** | Programmatic GraphQL schema building | [Repo](https://github.com/Sensorfactdev/graphql-schema-builder) |
| **pubsub-store** | Event-driven pub/sub pattern store | [Repo](https://github.com/Sensorfactdev/pubsub-store) |
| **ansible-role-aws-cloudwatch-logs-agent** | Historical Ansible + CloudWatch | [Repo](https://github.com/Sensorfactdev/ansible-role-aws-cloudwatch-logs-agent) |

## How Your Experience Maps

| Likely Requirement | Your Relevant Experience |
|-------------------|------------------------|
| Sensor data pipeline | GLP credit data pipeline, Lakehouse streaming pipeline |
| Time-series processing | Factor computation engine at Baiquan (daily market data) |
| Data quality handling | Quarantine-and-replay pattern in Lakehouse, schema validation at GLP |
| Streaming ingestion | Structured Streaming with Auto Loader, checkpoint-based fault tolerance |
| Aggregation/analytics | Medallion Architecture Bronze→Silver→Gold transformations |
| Scalability | PySpark for distributed processing, 3000+ securities at Baiquan |
| Python best practices | Expert Python, CI/CD, testing, type hints |

## Preparation Strategy

### Before the Assignment
1. **Read ALL 4 public assignments** in detail — understand evaluation criteria
2. **Set up a Python project template** with: pytest, mypy, Docker, Makefile
3. **Familiarize with ClickHouse**: basic DDL, INSERT, query syntax for time-series
4. **Review Kafka basics**: producers, consumers, topics, partitions
5. **Practice Prefect**: simple DAG, task decorators, flow orchestration

### During the Assignment
1. Start with a README explaining your approach and trade-offs
2. Build incrementally — working code beats incomplete ambition
3. Include tests (they value software engineering practices)
4. Document any assumptions
5. Leave a "what I would do with more time" section

### Technical Topics to Prepare for Assignment Review
1. **Kafka → Flink → ClickHouse**: How to handle late-arriving sensor data?
2. **Exactly-once semantics** across the pipeline
3. **Prefect vs Airflow**: Why Prefect? (Pythonic, dynamic DAGs, cloud-native)
4. **ClickHouse vs InfluxDB/TimescaleDB**: Why ClickHouse? (Column-oriented, fast aggregations, SQL-native)
5. **NATS vs Kafka**: Lightweight pub/sub vs persistent replay (they use both)
6. **Hasura + GraphQL**: How it auto-generates GraphQL from Postgres/ClickHouse
7. **Data quality at scale**: How to validate sensor readings in real-time?
