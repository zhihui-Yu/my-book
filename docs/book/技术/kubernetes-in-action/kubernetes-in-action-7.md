# Kubernetes-in-action (七)

---

> 本节内容：Deployment，StatefulSet

### Deployment

#### 作用

- 作为RC和RS的高一级资源 [RC -> replicationController, RS -> ReplicaSet]
- 可以让pod 模板变化后立即生效，不需要手动重启pod来让配置生效。 (会自动删除重建)
- 对于滚动升级友好，不需要额外允许多条命令来执行升级

#### 实践

- 使用ReplicationController来进行滚动升级
    - 蓝绿部署： 创建新的pod -> 将service改成选中新的pod ->
      新pod功能可以，则删除旧的pod，不可以则回滚service的选择器。 [不接受服务暂时不可用情况下]
    - 修改rc文件中的pod模板 -> 删除旧的pod [可以接受暂时服务不可用]

```yaml
apiVersion: v1
kind: ReplicationController
metadata:
  name: kubia-v1
spec:
  replicas: 3
  template:
    metadata:
      name: kubia
      labels:
        app: kubia
    spec:
      containers:
        - image: luksa/kubia:v1
          name: nodejs
---
apiVersion: v1
kind: Service
metadata:
  name: kubia
spec:
  type: LoadBalancer
  selector:
    app: kubia
  ports:
    - port: 8000
      targetPort: 8080
```

- 使用Deployment来进行滚动升级
    - 部署后，升级镜像并查看容器结果：
        - `kubectl create -f kubia-deployment-and-service-v1.yaml --record` # 指定 --record 则在查看历史版本时可以知道改版本修改了什么，
          既 CHANGE-CAUSE
        - `kubectl set image deployment kubia nodejs=luksa/kubia:v3` # 更新镜像，从而升级。
        - `kubectl rollout status deployment kubia` # 执行上面指令后，可以执行这个指令查看升级过程
        - `while true; do curl localhost:8000; sleep 1s; done;` # 一直调用service，看容器是否升级成功
        - `kubectl rollout history deployment kubia` # 查看可以回滚的版本
        - `kubectl rollout undo deployment kubia --to-revision=1` ## 回滚指定版本，不加后面的--的参数则是回滚到上个版本
        - `kubectl rollout pause deployment kubia`  # 暂停升级, 暂停都不能继续升级，恢复后才能。
        - `kubectl rollout resume deployment kubia` # 恢复升级

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kubia
spec:
  replicas: 3
  minReadySeconds: 10 # 设置就绪多久pod才算ready，才能被访问
  strategy: # 配置升级速率
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
    type: RollingUpdate
  selector:
    matchLabels:
      app: kubia
  template:
    metadata:
      name: kubia
      labels:
        app: kubia
    spec:
      containers:
        - image: luksa/kubia:v1
          name: nodejs
          readinessProbe: # 就绪探针
            periodSeconds: 1
            httpGet:
              path: /
              port: 8080

---
apiVersion: v1
kind: Service
metadata:
  name: kubia
spec:
  type: LoadBalancer
  selector:
    app: kubia
  ports:
    - port: 8000
      targetPort: 8080
```

#### 注意

- 为什么kubectl rolling-update已经过时
    - 由于rolling-update是由kubectl执行，然后同步到kube api-server，所以如果出现网络问题，会导致升级处于中间态，需要手动修复。
- deployment的pod name组成
    - metadata.name + deployment 模板的 hash + 随机数
- deployment 升级策略
    - Recreate 策略在删除旧的pod之后才开始创建新的pod
    - RollingUpdate 策略会渐进地删除旧的pod，与此同时创建新的
      pod，使应⽤程序在整个升级过程中都处于可⽤状态，并确保其处理请求的能⼒没有因为升级⽽有所影响。 [默认的]
        - 设置的期望副本数为3，上述的两个属性都设置为25%, maxSurge 允许最多pod数量达到 4，同时 maxUnavailable
          不允许出现任何不可⽤的pod [结果四舍五入]
        - 这两个参数用于升级时候的速率控制
- 升级后rs为什么还在
    - 因为回滚时候会用上rs模板中的pod模板来生成指定版本的pod。revisionHistoryLimit默认为 10，保留是十个版本。
- 升级失败怎么办
    - progressDeadlineSeconds参数设置了多久升级未完成则为失败，如果pod没有默认的值，则只能自己手动undo这次升级，不然就会一直停着。

### StatefulSet

#### 作用

- Stateful pod的允许需要持久卷的支持，pod内产生的数据需要持久化，StatefulSet 则是管理 Stateful Pod的资源
- StatefulSet 生成的pod后缀都是从下表-0开始， pod-0,pod-1,pod-2, 只有当第一个生成完才会生成第二个。

#### 实践

- 配置一个statefulSet，包含一个pod，三个副本，每个副本都绑定到一个pv上。
    - 修改pod的副本数量 `kubectl edit statefulSet kubia`
    - 删除pod时，pv和pvc依旧在，是因为防止误操作导致数据丢失，所以只能手动删除。
```yaml
apiVersion: v1
kind: Service
metadata:
  name: kubia
spec:
  clusterIP: None # headless
  selector:
    app: kubia
  ports:
    - name: http
      port: 8000
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: kubia
spec:
  serviceName: kubia
  replicas: 2
  selector:
    matchLabels:
      app: kubia # has to match .spec.template.metadata.labels
  template:
    metadata:
      labels:
        app: kubia
    spec:
      containers:
        - name: kubia
          image: luksa/kubia-pet
          ports:
            - name: http
              containerPort: 8080
          volumeMounts:
            - name: data
              mountPath: /var/data
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        resources:
          requests:
            storage: 1Mi
        accessModes:
          - ReadWriteOnce
```
- 使用kube proxy来在一个pod中访问另一个pod
    - 使用命令 `kubectl proxy` 生成proxy
    - `curl localhost:8001/api/v1/namespaces/default/pods/kubia-0/proxy/` #访问pod，最后的`/`必须加，因为api server解析流程如下
      - proxy将 `/api/v1/namespaces/default/pods/kubia-0/proxy/` 转发给 api server
      - api server 将访问pod的 `/` 路径既`pod-host:port/`, 如果没有最后的斜杠，则被认为只是访问api server而不是转发请求。
- 模拟节点失效导致statefulSet的pod状态无感知
  - 关闭某个node的网卡 `ifconfig eth0 down`
  - pod 变成 `unknown` 状态， 坏node上的kubectl没办法通知api server 当前pod的状态。
  - 在好的node上增加一个pod
  - 在好的node上执行删除故障node上的pod， 除非强制删除不然删不掉，因为pod本身就是terminating。 `kubectl delete pod name --force --grace-period 0`

#### 注意

- 有状态的pod需要保证集群内部不会出现两个一样名称的pod。 (如果出现一样的，则数据可能会重复执行)
    - 当有状态的pod被分配到多个node中时，其中一个node断开连接， pod不会执行删除重建，而是等待失联的node重连后告知pod的最新状态。