# Kubernetes-in-action (六)

---

> 本节内容：downward api, kube api-server

### Downward API

#### 作用

- 让容器拥有pod配置中的值，如namespace，pod-name，cup limits等等。
- 可以把值当成环境变量或者问卷挂载到pod。

#### 实践

- 使用pod的配置当成环境变量
    - 检查：`kubectl exec downward -- env`  # 查看环境变量

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: downward
spec:
  containers:
    - name: main
      image: busybox
      command: [ "sleep", "9999999" ]
      resources:
        requests:
          cpu: 15m
          memory: 5Mi
        limits:
          cpu: 100m
          memory: 10Mi
      env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: POD_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        - name: POD_IP
          valueFrom:
            fieldRef:
              fieldPath: status.podIP
        - name: NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
        - name: SERVICE_ACCOUNT
          valueFrom:
            fieldRef:
              fieldPath: spec.serviceAccountName
        - name: CONTAINER_CPU_REQUEST_MILLICORES
          valueFrom:
            resourceFieldRef:
              resource: requests.cpu
              divisor: 1m
        - name: CONTAINER_MEMORY_LIMIT_KIBIBYTES
          valueFrom:
            resourceFieldRef:
              resource: limits.memory
              divisor: 1Ki
```

- 使用pod的配置当成卷文件挂载
    - 查看卷文件：`kubectl exec downward -- ls -lL /etc/downward`

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: downward
  labels:
    foo: bar
  annotations:
    key1: value1
    key2: |
      multi
      line
      value
spec:
  containers:
    - name: main
      image: busybox
      command: [ "sleep", "9999999" ]
      resources:
        requests:
          cpu: 15m
          memory: 5Mi
        limits:
          cpu: 100m
          memory: 10Mi
      volumeMounts:
        - name: downward
          mountPath: /etc/downward
  volumes:
    - name: downward
      downwardAPI:
        items:
          - path: "podName"
            fieldRef:
              fieldPath: metadata.name
          - path: "podNamespace"
            fieldRef:
              fieldPath: metadata.namespace
          - path: "labels"
            fieldRef:
              fieldPath: metadata.labels
          - path: "annotations"
            fieldRef:
              fieldPath: metadata.annotations
          - path: "containerCpuRequestMilliCores"
            resourceFieldRef:
              containerName: main
              resource: requests.cpu
              divisor: 1m
          - path: "containerMemoryLimitBytes"
            resourceFieldRef:
              containerName: main
              resource: limits.memory
              divisor: 1
```

#### 注意

- 只能将某些配置传入pod，并不是所有
- 使用环境变量时，修改配置文件，pod的环境变量不会变，但是使用卷会变。
- 定义卷字段时，要申明容器名称， 好处是可以给容器添加其他容器的配置值

### Kube API Server

#### 作用

- 存储了集群信息, 各种资源类型可定义的api version
- 可以通过rest api 获取各种资源的信息

#### 实践

- 使用kube proxy与api server交互

```shell
kubectl proxy # 开启一个proxy
curl http://localhost:8001/apis # 查看server支持的api
curl http://localhost:8001/apis/batch/v1/namespaces/default/jobs/my-job # 查看具体的资源信息
```

- 在pod内部调用api server
    - 创建一个内部有curl工具的pod: `kubectl exec -it curl-with-ambassador sh` # 进去容器
    - 在内部调用api server的endpoint (REST API):
        - `curl -H "Authorization: Bearer $(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" --cacert /var/run/secrets/kubernetes.io/serviceaccount/ca.crt https://kubernetes/api/v1`

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: curl
spec:
  containers:
    - name: main
      image: curlimages/curl:7.87.0
      command: [ "sleep", "9999999" ]
```

- 在pod中使用代理与api server交互
    - 在pod中定义两个容器，一个proxy，一个含curl的容器: `kubectl exec -it curl-with-ambassador -c main sh` # 进去容器
    - 在含curl工具的容器中访问proxy以达到访问api server效果: `curl localhost:8001/api`

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: curl-with-ambassador
spec:
  containers:
    - name: main
      image: curlimages/curl:7.87.0
      command: [ "sleep", "9999999" ]
    - name: ambassador
      image: luksa/kubectl-proxy:1.6.2
```

- 客户端工具与api server交互
    - go - https://github.com/kubernetes/client-go
    - java - https://github.com/fabric8io/kubernetes-client