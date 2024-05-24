# Kubernetes-in-action (二)

---

> 本节内容：Probe,ReplicaSet,DaemonSet,Job

## 探针

#### 作用

- 用来探测程序是否处于正常状态, 异常如JVM OOM，死锁导致无法处理请求。

#### 探测容器的机制

- HTTP GET探针： 对程序进行http get 请求，响应异常既pod需要重启
- TCP套接字探针：与程序进行TCP连接，失败则重启
- Exec探针： 在容器内执行任意命令，并查看退出码，如果非0，则需要重启。

#### 实践

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: kubia-liveness
spec:
  containers:
    - image: luksa/kubia-unhealthy
      name: kubia
      livenessProbe: # 配置探针
        httpGet:
          path: /
          port: 8080
        initialDelaySeconds: 15 # 由于探针会在pod创建时就执行，可能进程还没启动，所以设置延迟执行
```

## ReplicationController

#### 作用

- 管理pod，弹性伸缩。 如果pod是单独创建的，那么node节点故障时，不会被重建，但是使用ReplicationController后，会在其他node上重建pod，并保证数量一致。
- 一般使用label来识别该pod是否被管控

#### 实践

```yaml
apiVersion: v1
kind: ReplicationController
metadata:
  name: kubia
spec:
  replicas: 3
  selector:
    app: kubia
  template:
    metadata:
      labels:
        app: kubia
    spec:
      containers:
        - name: kubia
          image: luksa/kubia
          ports:
            - containerPort: 8080
```

- `kubectl scale rc kubia --replicas=10` # 扩容
- `kubectl edit rc kubia` # 修改文件的配置，并且保存后立即生效
- `kubectl delete rc kubia --cascade=false` # 删除RC但是不删除pod

#### 注意事项

- 如果修改了pod 的标签，那么RC会新建pod，因为RC是根据标签来判断的。
    - `kubectl label pod kubia-tm2jw app=foo --overwrite` # 修改label
- 如果修改了RC文件种的匹配标签，那么会创建出新的pod，旧的pod就不被管理了
- 修改RC种pod的template时候，并不会马上作用于现在的pod上，需要删除旧的才会有新的。

## ReplicaSet

#### 作用

- 与ReplicationController相似，但是在其基础上提供更丰富的声明表达，现在基本都是用RS而不是RC。
- 如RC只能管理具有指定的某些label的pod，后者对label的管理可以是匹配其中之一，或者全不匹配等等

#### 实践

- 使用 matchLabels 来管理pod

```yaml
apiVersion: apps/v1beta2 #如果你的有问题，则用apps/v1
kind: ReplicaSet
metadata:
  name: kubia
spec:
  replicas: 3
  selector:
    matchLabels:
      app: kubia
  template:
    metadata:
      labels:
        app: kubia
    spec:
      containers:
        - name: kubia
          image: luksa/kubia
```

- 使用 matchExpressions 来管理pod

```yaml
apiVersion: apps/v1beta2
kind: ReplicaSet
metadata:
  name: kubia
spec:
  replicas: 3
  selector:
    matchExpressions:
      - key: app
        operator: In # NotIn, Exists, DoesNotExist
        values:
          - kubia
  template:
    metadata:
      labels:
        app: kubia
    spec:
      containers:
        - name: kubia
          image: luksa/kubia
```

- 删除RS命令： `kubectl delete rs kubia` # 删除rs包括pod

## DaemonSet

#### 作用

- 它不关心副本数量，只关心为每个符合的node都要建一个pod

#### 实践

- 创建一个ds

```yaml
apiVersion: apps/v1beta2
kind: DaemonSet
metadata:
  name: ssd-monitor
spec:
  selector:
    matchLabels:
      app: ssd-monitor
  template:
    metadata:
      labels:
        app: ssd-monitor
    spec:
      nodeSelector:
        disk: ssd
      containers:
        - name: main
          image: luksa/ssd-monitor
```

- get ds 信息： `kubectl get d`
- 给node加label： `kubectl label node node-name disk=ssd`
- 修改node的label： `kubectl label node node-name disk=hdd --overwrite` # 修改后，pod会被删除

## Job

#### 作用
- 完成临时任务后销毁pod

#### 实践
- 查看job： `kubectl get job`
- 创建一个普通job
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: batch-job
spec:
  template:
    metadata:
      labels:
        app: batch-job
    spec:
      restartPolicy: OnFailure # job 不能使用默认的always，因为执行完就要被销毁
      containers:
      - name: main
        image: luksa/batch-job
```
- 创建一个执行多次的job
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: multi-completion-batch-job
spec:
  completions: 5 # 执行5次，会创建5次pod
  parallelism: 2 # 同时启动两个pod来执行任务
  activeDeadlineSeconds: 10 # 超过这个时间认为失败，并终止pod
  backoffLimit: 1 # 允许的失败次数，默认是6
  template:
    metadata:
      labels:
        app: batch-job
    spec:
      restartPolicy: OnFailure
      containers:
      - name: main
        image: luksa/batch-job
```
- 创建CronJob
```yaml
apiVersion: batch/v1beta1
kind: CronJob
metadata:
  name: batch-job-every-fifteen-minutes
spec:
  schedule: "0,15,30,45 * * * *" # 每小时的第几分钟 + 四个星号： 每天第几个小时， 每月的第几天，每年的第几个月，每周的第几天
  startingDeadlineSeconds: 15 # 允许开始的截至时间，当前表示开始后15s如果还没启动，任务就不允许，当初failed处理
  jobTemplate:
    spec:
      template:
        metadata:
          labels:
            app: periodic-batch-job
        spec:
          restartPolicy: OnFailure
          containers:
          - name: main
            image: luksa/batch-job
```