# [Milvus](https://milvus.io/docs/overview.md)

---

> 官方: https://milvus.io/docs/overview.md <br/>
> 中文: https://www.milvus-io.com/overview

## [介绍](https://www.milvus-io.com/overview)
- 是一种向量数据库
- Milvus是在2019年创建的，其唯一目标是存储、索引和管理由深度神经网络和其他机器学习（ML）模型生成的大规模嵌入向量。
- 作为一个专门设计用于处理输入向量查询的数据库，它能够处理万亿级别的向量索引。

## docker 安装 Milvus 并使用 Attu 可视化工具
- 使用docker-compose安装 
  - `docker-compose -f milvus-standalone-docker-compose.yml up -d`
- 本地浏览器启动 http://localhost:8000/ 
  - Milvus的host是默认的， 用的是docker container name [所有的容器都在一个网络下，所以可以这样访问]

> 文档地址：
> Milvus: https://github.com/milvus-io/milvus/releases
> Attu: https://github.com/zilliztech/attu/releases


## [Milvus JAVA SDK](https://www.milvus-io.com/install-java)

> index type: https://milvus.io/docs/index.md#floating


## docker install
```dockerfile
version: '3.5'

services:
  etcd:
    container_name: milvus-etcd
    image: quay.io/coreos/etcd:v3.5.5
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
      - ETCD_SNAPSHOT_COUNT=50000
    volumes:
      - ${DOCKER_VOLUME_DIRECTORY:-.}/volumes/etcd:/etcd
    command: etcd -advertise-client-urls=http://127.0.0.1:2379 -listen-client-urls http://0.0.0.0:2379 --data-dir /etcd
    healthcheck:
      test: ["CMD", "etcdctl", "endpoint", "health"]
      interval: 30s
      timeout: 20s
      retries: 3

  minio:
    container_name: milvus-minio
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    ports:
      - "9001:9001"
      - "9000:9000"
    volumes:
      - ${DOCKER_VOLUME_DIRECTORY:-.}/volumes/minio:/minio_data
    command: minio server /minio_data --console-address ":9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  standalone:
    container_name: milvus-standalone
    image: milvusdb/milvus:v2.3.9
    command: ["milvus", "run", "standalone"]
    security_opt:
    - seccomp:unconfined
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    volumes:
      - ${DOCKER_VOLUME_DIRECTORY:-.}/volumes/milvus:/var/lib/milvus
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9091/healthz"]
      interval: 30s
      start_period: 90s
      timeout: 20s
      retries: 3
    ports:
      - "19530:19530"
      - "9091:9091"
    depends_on:
      - "etcd"
      - "minio"
  
  attu:
    container_name: attu
    image: zilliz/attu:v2.3.8
    environment:
      MILVUS_URL: standalone:19530
    ports:
      - "8000:3000"
    depends_on:
      - "standalone"

networks:
  default:
    name: milvus
```