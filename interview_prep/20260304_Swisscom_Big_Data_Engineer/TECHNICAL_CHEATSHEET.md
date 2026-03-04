# Swisscom Big Data Engineer - Technical Cheatsheet
**Interview**: 2026-03-04 10:00 CET | Yannis Klonatos (EPFL PhD, Query Optimization) + Mani

---

## CORE NUMBERS

**Personal**: 6 yrs exp | 8.2 GPA (VU Amsterdam AI) | 3K+ securities (Baiquan) | Databricks Professional (2026-01)
**Project**: 26 fields | Top 100 coins | 5-min pull | ~29K records/day | 30s trigger | 10-min watermark | 85% ↓ files | 6.7x faster | <0.1% quarantine
**Swisscom**: Billions events/day | 2TB/day | 4-person team

---

## SPARK INTERNALS

### Catalyst Optimizer (4 Phases)
1. **Unresolved Logical Plan**: Parse SQL/DataFrame → AST (no validation)
2. **Resolved Logical Plan**: Catalog lookup → validate tables/columns/types
3. **Optimized Logical Plan**: Rule-based optimization
   - Predicate Pushdown: Move filters to scan (file-level skip in Parquet)
   - Column Pruning: Read only needed columns (columnar storage benefit)
   - Constant Folding: Compute `100*2` at compile time → `200`
   - Join Reordering: Small tables first (reduce intermediate results)
4. **Physical Plan**: Cost-based optimization (CBO)
   - Requires: `ANALYZE TABLE t COMPUTE STATISTICS FOR COLUMNS`
   - Estimates: row count, data size, cardinality, min/max, null ratio
   - Selects: Broadcast vs Shuffle Hash vs Sort Merge Join

### Tungsten Execution Engine (3 Optimizations)
1. **Off-heap Memory Management**
   - Binary format (not Java objects) → 5-10x less memory
   - No GC overhead (JVM doesn't scan off-heap data)
   - Example: Row object ~100 bytes → binary ~13 bytes
2. **Cache-aware Computation**
   - Contiguous memory layout → high CPU cache hit rate
   - L1 cache ~1ns, main memory ~100ns (100x difference)
3. **Whole-stage Code Generation**
   - Fuse operators into single generated method
   - Eliminate virtual function calls (~10ns each)
   - JIT compiler can inline/optimize further

**Key Concept**: "Abstraction Without Regret" (Yannis's LegoBase paper) — high-level code compiles to C-like performance

---

## SHUFFLE MECHANISM

### How Shuffle Works
1. **Map**: Each executor processes local data → outputs (key, value) pairs
2. **Partition Calculation**: `partition_id = hash(key) % num_partitions`
3. **Shuffle Write**: Write to local disk, grouped by partition
4. **Shuffle Read**: Executors pull data over network
5. **Reduce**: Process data within each partition

### Three Costs
- **Disk I/O**: Write intermediate data to disk (100x slower than memory)
- **Network Transfer**: Move data between executors (bandwidth bottleneck)
- **Serialization**: Convert objects to bytes and back (CPU overhead)

### Key Insight
- **Partition ≠ Executor**: Partition = logical data split, Executor = physical compute resource
- One executor processes multiple partitions (typically 2-3x num cores)
- Same key always goes to same partition (hash determinism)

---

## JOIN STRATEGIES

| Strategy | When | Shuffle | Memory | Speed | Formula |
|----------|------|---------|--------|-------|---------|
| **Broadcast Hash** | Small table <10MB | ❌ | Small table fits in each executor | Fastest | `broadcast(small_df)` |
| **Shuffle Hash** | One table smaller | ✅ | Small table partition fits in memory | Fast | Auto-selected |
| **Sort Merge** | Both tables large | ✅ | Only 2 pointers needed | Slow | Default for large joins |

### Sort Merge Join Deep Dive
1. **Shuffle**: Both tables by join key → `hash(key) % num_partitions`
2. **Sort**: Within each partition, sort both tables by join key
3. **Merge**: Two-pointer algorithm (like merging sorted arrays)
   - Pointer A on table A, pointer B on table B
   - If `A.key == B.key` → match, output, advance B
   - If `A.key < B.key` → advance A
   - If `A.key > B.key` → advance B
4. **Complexity**: O(n log n) sort + O(n+m) merge

**Why Sort?** Enables linear scan (no backtracking), memory-efficient (no hash table)

---

## DATA SKEW

### Detection
- Spark UI: Task duration/input size 10x+ difference
- Code: `df.groupBy("key").count().orderBy("count", desc=True)`
- Partition size: `rdd.mapPartitionsWithIndex(lambda i,it: [(i, sum(1 for _ in it))])`

### Solutions

| Method | Use Case | How | Trade-off |
|--------|----------|-----|-----------|
| **Salting** | GroupBy skew | Add random suffix to hot keys → 2-stage aggregation | +1 stage, complex code |
| **Broadcast Join** | Join skew, small table | Avoid shuffle entirely | Small table must fit in memory |
| **Split Processing** | Few hot keys | Process hot keys separately (broadcast), normal keys normally, union | Manual key identification |
| **Increase Partitions** | Mild skew | `spark.sql.shuffle.partitions = 1000` | More scheduling overhead |
| **AQE (Spark 3.0+)** | General | Auto-detect & split skewed partitions at runtime | Limited for extreme skew |

### Salting Example
```python
# Hot key: user_id=101 (1M records)
# Add suffix _0 to _9 → 10 keys (100K each)
df.withColumn("salted", when(col("user_id")==101,
    concat(col("user_id"), lit("_"), (rand()*10).cast("int"))
).otherwise(col("user_id")))
# Aggregate by salted → remove suffix → aggregate again
```

---

## STREAMING CONCEPTS

### Checkpoint
- **Purpose**: Exactly-once semantics + fault tolerance
- **Contents**: `offsets/` (batch ranges), `commits/` (completion markers), `state/` (stateful ops), `metadata`
- **Recovery**: Read last commit → resume from last offset → reprocess uncommitted batches
- **Location**: S3/HDFS (reliable storage)

### Watermarking
- **Formula**: `watermark = max(event_time) - threshold`
- **Global Watermark**: `min(all partition watermarks)` (slowest partition determines)
- **Purpose**: When to stop waiting for late data in event-time windows
- **My Choice**: 10-min watermark (based on P99 latency ~8 min)
- **Trade-off**: Larger → more complete but higher latency; Smaller → faster but drop late data

### Structured Streaming
- **Model**: Treat stream as unbounded table, micro-batch processing
- **Trigger Interval**: How often to process (e.g., 30s)
- **Output Modes**: Append (new rows), Complete (full result), Update (changed rows)

---

## DATA ARCHITECTURE

### Medallion Architecture
| Layer | Format | Schema | Purpose | Example |
|-------|--------|--------|---------|---------|
| **Bronze** | JSON | Schema-on-read | Raw ingestion, audit trail, replay | All API responses |
| **Silver** | Parquet | Enforced | Cleaned, validated, queryable | Validated transactions |
| **Gold** | Parquet | Business views | Aggregated, denormalized | Daily revenue by region |

**Principle**: Never discard data. Bronze captures everything, Silver cleans, Gold aggregates.

### Quarantine-and-Replay Pattern
```
Bronze (all data) → Validation → Pass → Silver
                              → Fail → Quarantine table (raw_data, error_reason, timestamp)
                                    → Fix schema/logic → Replay → Silver
```
**Why?** Data loss is expensive, storage is cheap. Quarantine enables post-hoc fixes.

### Star Schema vs Snowflake
- **Star**: 1 fact table + N dimension tables (direct joins) → Simple queries, fast
- **Snowflake**: Dimensions normalized (e.g., location → city → country) → Less storage, more joins
- **Recommendation**: Star for analytics (query speed > storage)

---

## SQL PATTERNS

### Window Functions
```sql
-- Top N per group
ROW_NUMBER() OVER (PARTITION BY category ORDER BY revenue DESC)

-- Cumulative sum
SUM(amount) OVER (ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)

-- Previous/next row
LAG(price, 1) OVER (ORDER BY date)
LEAD(price, 1) OVER (ORDER BY date)
```

### SCD Type 2 (Slowly Changing Dimension)
```sql
MERGE INTO dim_users target
USING source_users source
ON target.user_id = source.user_id AND target.is_current = true
WHEN MATCHED AND target.name != source.name THEN
  UPDATE SET is_current = false, valid_to = current_date()
WHEN NOT MATCHED THEN
  INSERT (user_id, name, is_current, valid_from, valid_to)
  VALUES (source.user_id, source.name, true, current_date(), '9999-12-31')
```

### Query Optimization
```sql
-- Bad: Full table scan
SELECT * FROM orders WHERE YEAR(order_date) = 2026

-- Good: Partition pruning (if partitioned by order_date)
SELECT * FROM orders WHERE order_date >= '2026-01-01' AND order_date < '2027-01-01'
```

---

## DELTA LAKE

### Core Features
- **ACID Transactions**: Serializable isolation, concurrent writes
- **Time Travel**: `SELECT * FROM table VERSION AS OF 10` or `TIMESTAMP AS OF '2026-01-01'`
- **Schema Enforcement**: Reject writes with incompatible schema (unless `mergeSchema=true`)
- **Schema Evolution**: Add columns with `mergeSchema`, change types with `overwriteSchema`

### Z-ordering vs Liquid Clustering
| Feature | Z-ordering | Liquid Clustering |
|---------|-----------|-------------------|
| Introduced | 2019 | 2023 (GA) |
| Optimization | Manual `OPTIMIZE ZORDER BY (col1, col2)` | Automatic |
| With Partitioning | ✅ Compatible | ❌ Mutually exclusive |
| Use Case | Learning/control | Production (recommended) |

**My Choice**: Z-ordering (learning project, manual control). Production → Liquid Clustering.

### Optimization Commands
```sql
-- Compact small files
OPTIMIZE table_name

-- Z-order (co-locate data by columns)
OPTIMIZE table_name ZORDER BY (symbol, timestamp)

-- Vacuum (delete old files, default 7-day retention)
VACUUM table_name RETAIN 168 HOURS
```

---

## PERFORMANCE TUNING

### Partition Tuning
```python
# Default shuffle partitions
spark.conf.get("spark.sql.shuffle.partitions")  # 200

# Rule of thumb: 2-3x num cores
# 3 machines × 4 cores = 12 cores → 24-36 partitions
spark.conf.set("spark.sql.shuffle.partitions", "36")

# Manual repartition
df.repartition(36, "user_id")  # Shuffle
df.coalesce(10)  # No shuffle (only reduce)
```

### AQE (Adaptive Query Execution)
```python
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")  # Merge small partitions
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")  # Handle skew
```

### Caching Strategy
```python
# Cache in memory (deserialized)
df.cache()  # or df.persist(StorageLevel.MEMORY_ONLY)

# Cache in memory + disk (serialized)
df.persist(StorageLevel.MEMORY_AND_DISK)

# Unpersist when done
df.unpersist()
```

---

## KAFKA & STREAMING

### Kafka Core Concepts
- **Topic**: Logical channel (e.g., `network_events`)
- **Partition**: Physical split of topic (parallelism unit)
- **Consumer Group**: Consumers share partitions (each partition → 1 consumer)
- **Offset**: Position in partition (commit offset = mark as processed)
- **Replication Factor**: Copies of each partition (fault tolerance)

### Exactly-Once Semantics
1. **Idempotent Producer**: Deduplicate retries (producer-side)
2. **Transactional Writes**: Atomic commit across partitions
3. **Checkpoint**: Store offsets in reliable storage
4. **Idempotent Sink**: Use `MERGE` instead of `INSERT` (consumer-side)

### Spark + Kafka
```python
df = spark.readStream \
  .format("kafka") \
  .option("kafka.bootstrap.servers", "localhost:9092") \
  .option("subscribe", "topic") \
  .option("startingOffsets", "earliest") \
  .load()

query = df.writeStream \
  .format("delta") \
  .option("checkpointLocation", "s3://bucket/checkpoint") \
  .trigger(processingTime="30 seconds") \
  .start("s3://bucket/output")
```

---

## DOCKER & CONTAINERS

### Core Concepts
- **Image**: Read-only template with application + dependencies (layered filesystem)
- **Container**: Running instance of image (isolated process, not VM)
- **Layer**: Each Dockerfile instruction creates a layer (cached, immutable)
- **Union Filesystem**: Overlay layers to create single view (copy-on-write)

### Dockerfile Best Practices
```dockerfile
# Multi-stage build (reduce image size)
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
COPY . /app
CMD ["python", "app.py"]
```

**Key Points**:
- Use `.dockerignore` to exclude unnecessary files (reduce build context)
- Minimize layers: combine RUN commands with `&&`
- Order matters: put frequently changing layers last (leverage cache)
- Use specific tags, not `latest` (reproducibility)

### Docker Networking
- **Bridge**: Default, containers on same host communicate
- **Host**: Container uses host's network (no isolation, better performance)
- **Overlay**: Multi-host networking (Swarm/Kubernetes)

### Volume vs Bind Mount
- **Volume**: Managed by Docker (`/var/lib/docker/volumes/`), best for persistence
- **Bind Mount**: Mount host directory, good for development (hot reload)

### My Experience
"In Financial Lakehouse, I containerized Spark jobs with Docker. Used multi-stage builds to reduce image from 2GB to 500MB. Mounted config files as volumes for environment-specific settings without rebuilding images."

---

## KUBERNETES (K8S)

### Architecture
```
Master Node (Control Plane):
  - API Server: Entry point for all operations
  - Scheduler: Assigns pods to nodes
  - Controller Manager: Maintains desired state
  - etcd: Distributed key-value store (cluster state)

Worker Nodes:
  - Kubelet: Agent that runs pods
  - Kube-proxy: Network proxy (service routing)
  - Container Runtime: Docker/containerd
```

### Core Resources

#### Pod
- Smallest deployable unit (1+ containers)
- Shares network namespace (localhost communication)
- Ephemeral: no guaranteed persistence

#### Deployment
- Manages ReplicaSets (desired pod count)
- Rolling updates: gradually replace old pods
- Rollback: revert to previous version

#### Service
- Stable endpoint for pods (pods are ephemeral, IPs change)
- **ClusterIP**: Internal only (default)
- **NodePort**: Expose on each node's IP
- **LoadBalancer**: Cloud provider LB (AWS ELB)

#### ConfigMap & Secret
- **ConfigMap**: Non-sensitive config (env vars, files)
- **Secret**: Sensitive data (base64 encoded, not encrypted by default)

### Resource Management
```yaml
resources:
  requests:    # Minimum guaranteed
    memory: "1Gi"
    cpu: "500m"
  limits:      # Maximum allowed
    memory: "2Gi"
    cpu: "1000m"
```

**Key Insight**:
- `requests` → scheduling decision (node must have this available)
- `limits` → runtime enforcement (pod killed if exceeded)

### Horizontal Pod Autoscaler (HPA)
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

**How it works**: Metrics Server collects CPU/memory → HPA adjusts replicas based on target

### Persistent Storage
- **PersistentVolume (PV)**: Cluster-level storage resource
- **PersistentVolumeClaim (PVC)**: User request for storage
- **StorageClass**: Dynamic provisioning (AWS EBS, GCP PD)

### My Experience (Honest)
"I have Docker experience from Financial Lakehouse but limited K8s production experience. I understand core concepts—pods, deployments, services—and resource management. I've deployed test applications locally with Minikube. For production, I'd leverage Helm charts and follow GitOps practices. Eager to deepen K8s expertise in this role."

---

## AIRFLOW

### Architecture
```
Scheduler: Parses DAGs, schedules tasks
Executor: Runs tasks (Local, Celery, Kubernetes)
Webserver: UI for monitoring
Metadata DB: Stores DAG runs, task states (Postgres/MySQL)
Workers: Execute tasks (Celery/K8s executor)
```

### DAG (Directed Acyclic Graph)
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'data-eng',
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': True,
}

with DAG(
    'etl_pipeline',
    default_args=default_args,
    schedule_interval='0 2 * * *',  # Daily at 2 AM
    start_date=datetime(2026, 1, 1),
    catchup=False,  # Don't backfill
) as dag:

    extract = PythonOperator(task_id='extract', python_callable=extract_data)
    transform = PythonOperator(task_id='transform', python_callable=transform_data)
    load = PythonOperator(task_id='load', python_callable=load_data)

    extract >> transform >> load  # Task dependencies
```

### Key Concepts

#### Operators
- **PythonOperator**: Execute Python function
- **BashOperator**: Run bash command
- **SparkSubmitOperator**: Submit Spark job
- **S3ToRedshiftOperator**: Data transfer (provider-specific)

#### Executors
- **SequentialExecutor**: One task at a time (dev only)
- **LocalExecutor**: Parallel tasks on single machine
- **CeleryExecutor**: Distributed workers (production)
- **KubernetesExecutor**: Each task = K8s pod (dynamic scaling)

#### XCom (Cross-Communication)
```python
# Push data
def extract(**context):
    data = fetch_data()
    context['ti'].xcom_push(key='raw_data', value=data)

# Pull data
def transform(**context):
    data = context['ti'].xcom_pull(key='raw_data', task_ids='extract')
```

**Limitation**: XCom stores in metadata DB → not for large data (use S3/HDFS instead)

### Scheduling
- **Cron expression**: `0 2 * * *` = daily at 2 AM
- **Timedelta**: `schedule_interval=timedelta(hours=6)` = every 6 hours
- **Catchup**: Backfill missed runs (default True, usually set False)

### Idempotency
**Critical**: Tasks should produce same result when re-run
- Use `MERGE` instead of `INSERT` (avoid duplicates)
- Check if output exists before processing
- Use execution_date in output paths (partition by date)

### Monitoring
- **Task States**: success, failed, running, skipped, upstream_failed
- **SLA**: Alert if task exceeds expected duration
- **Sensors**: Wait for external condition (S3KeySensor, TimeSensor)

### My Experience
"In Financial Lakehouse, I orchestrated Spark jobs with Airflow. Used KubernetesExecutor for dynamic scaling—each Spark job runs in isolated pod. Implemented idempotent tasks with Delta Lake MERGE. Set up SLA monitoring for critical pipelines. Catchup=False to avoid backfill storms after downtime."

---

## AWS (Core Services for Data Engineering)

### S3 (Simple Storage Service)
- **Object storage**: Key-value (not filesystem)
- **Bucket**: Top-level container (globally unique name)
- **Storage Classes**:
  - Standard: Frequent access
  - Intelligent-Tiering: Auto-move between tiers
  - Glacier: Archive (retrieval time: minutes to hours)

**Best Practices**:
- Use prefixes for partitioning: `s3://bucket/year=2026/month=01/day=15/`
- Enable versioning for critical data
- Lifecycle policies: auto-transition to cheaper storage
- Server-side encryption (SSE-S3, SSE-KMS)

### EMR (Elastic MapReduce)
- Managed Hadoop/Spark cluster
- **Transient clusters**: Spin up for job, terminate after (cost-effective)
- **Persistent clusters**: Long-running (faster job submission)
- **Instance types**: Master, Core (HDFS), Task (compute-only)

**Cost optimization**:
- Use Spot instances for Task nodes (70-90% cheaper)
- Auto-scaling: add/remove Task nodes based on YARN metrics

### Glue
- **Glue Crawler**: Auto-discover schema, populate Data Catalog
- **Glue ETL**: Serverless Spark jobs (Python/Scala)
- **Glue Data Catalog**: Hive-compatible metastore (shared with Athena, EMR)

**When to use**: Simple ETL, no complex orchestration. For complex pipelines → Airflow + EMR.

### Athena
- Serverless SQL query on S3 (Presto-based)
- Pay per query (scanned data)
- **Optimization**: Partition data, use Parquet/ORC, compress

**Use case**: Ad-hoc queries, BI tools. Not for heavy ETL (use Spark).

### Redshift
- Data warehouse (columnar storage)
- **Distribution styles**:
  - KEY: Distribute by column (co-locate join keys)
  - ALL: Replicate to all nodes (small dimension tables)
  - EVEN: Round-robin (default)
- **Sort keys**: Physical ordering (range queries)

**Best practices**:
- VACUUM to reclaim space after deletes
- ANALYZE to update statistics (query planner)
- Use COPY from S3 (parallel load, faster than INSERT)

### Kinesis
- Real-time streaming (like Kafka)
- **Kinesis Data Streams**: Low-level (manual shard management)
- **Kinesis Firehose**: Managed (auto-scaling, direct to S3/Redshift)

**Shard**: Partition unit (1 MB/s write, 2 MB/s read per shard)

### IAM (Identity and Access Management)
- **Principle of least privilege**: Grant minimum permissions
- **Roles**: Temporary credentials (better than access keys)
- **Policies**: JSON document defining permissions

```json
{
  "Effect": "Allow",
  "Action": ["s3:GetObject", "s3:PutObject"],
  "Resource": "arn:aws:s3:::my-bucket/data/*"
}
```

### VPC (Virtual Private Cloud)
- **Subnet**: IP range within VPC (public vs private)
- **Security Group**: Stateful firewall (instance-level)
- **NAT Gateway**: Allow private subnet to access internet

**Data engineering context**: EMR in private subnet, access S3 via VPC endpoint (no internet)

### My Experience
"In Financial Lakehouse, I used S3 for data lake (Bronze/Silver/Gold layers). Partitioned by date for efficient queries. Used Athena for ad-hoc analysis. For production ETL, I'd use EMR with Spot instances for cost optimization. Familiar with IAM roles for secure access—no hardcoded credentials."

---

## INTERVIEW RESPONSES

### "Explain Spark query execution"
"Catalyst parses SQL to AST, resolves via catalog, optimizes with rule-based transformations like predicate pushdown and column pruning, then generates physical plans. CBO selects best plan using table statistics. Tungsten compiles to binary format with whole-stage code generation, eliminating virtual calls and enabling JIT optimization."

### "How do you handle data skew?"
"Detect via Spark UI (10x task duration) or groupBy count. For GroupBy skew, use salting—add random suffix to hot keys, aggregate twice. For Join skew, broadcast small table or split hot keys for separate processing. Enable AQE for automatic runtime optimization."

### "What's the difference between RDD, DataFrame, Dataset?"
"RDD is low-level, no optimization. DataFrame has schema, Catalyst optimizes. Dataset adds compile-time type safety (Scala/Java). Use DataFrame/Dataset—let Catalyst optimize. RDD only for custom partitioning or low-level control."

### "Explain checkpoint in Structured Streaming"
"Checkpoint stores offsets (batch ranges), commits (completion markers), and state (for stateful ops) to S3. On failure, read last commit, resume from last offset, reprocess uncommitted batches. Enables exactly-once semantics and fault tolerance."

### "Why Sort Merge Join over Hash Join?"
"Sort Merge is memory-efficient—only needs two pointers, no hash table. For very large tables where Hash Join causes OOM, Sort Merge scales arbitrarily. Trade-off: O(n log n) sort cost vs O(1) hash lookup. Use when both tables too large for memory."

---

## QUESTIONS TO ASK

1. "What's the data pipeline architecture—Lambda, Kappa, or custom? How do you handle late-arriving events?"
2. "With 4 people at this scale, how do you balance feature development vs operational maintenance? What's on-call like?"
3. "What are the biggest technical challenges in the next 6-12 months?"

---

## WEAKNESSES BRIDGE

- **Scala**: "No production experience, but understand JVM + functional programming (immutability, HOF). PySpark API is functional. Confident I can ramp up quickly."
- **Telecom**: "Proven adaptability across 3 domains. Core data engineering challenges are universal: scale, quality, reliability."
- **Gap (2019-2023)**: "Deliberate career pivot: independent investing + language learning + grad school prep."

---

**Key**: Yannis values "why" over "how". Show trade-off thinking, not just API knowledge.
