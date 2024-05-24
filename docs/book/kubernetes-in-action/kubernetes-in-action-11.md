# Kubernetes-in-action (十一)

---

> 本节内容：
> 1. 基于CPU使⽤率配置pod的⾃动横向伸缩，了解Cluster Autoscaler
> 2. pod的节点选择：节点污点,节点亲缘性规则,节点⾮亲缘性的功能

## 基于CPU使⽤率配置pod的⾃动横向伸缩

#### 流程

![Autoscaler获取度量数据伸缩⽬标部署的⽅式](https://raw.githubusercontent.com/zhihui-Yu/images/main/kube-in-actions/C15-1.png)

#### 实践 （一）

- 部署一个deployment并设置其requests: `kubectl apply -f deployment.yaml`
- 配置其自动伸缩规则： `kubectl autoscale deployment kubia --cpu-percent=30 --min=1 --max=5`
- 查看deployment的HorizontalpodAutoscaler： `kubectl get hpa.v1.autoscaling kubia -o yaml`
- 运行一个脚本调用pod来提高cpu："while true; do curl http://10.42.0.117:8080 && echo `date`; done"
- 发现pod的数量增加了。

> - 保持cpu在[cpu-percent]30以下，并且pod最少1个，最多5个。 <br/>
> - Autoscaler: 单次扩容有时间和大小限制：pod >2,最多翻倍， 否则最大扩容到4个副本。
    时间：3分钟没有任何扩容操作则扩容，5min没有缩容操作则运行缩容。<br/>
> - 使用 kubectl edit hpa 来修改 hpa的属性
> - 不会将pod缩容到0.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kubia
spec:
  replicas: 3
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
          resources:
            requests:
              cpu: 100m
```

> 基于自定义指标实现伸缩：https://medium.com/@marko.luksa/kubernetes-autoscaling-based-on-custom-metrics-without-using-a-host-port-b783ed6241ac

### Cluster Autoscaler

- 作用：负责在由于节点资源不⾜，⽽⽆法调度某pod到已有节点时，⾃动部署新节点。它也会在节点长时间使⽤率低下的情况下下线节点

#### 集群扩容流程

![扩容流程](https://raw.githubusercontent.com/zhihui-Yu/images/main/kube-in-actions/C15-2.png)

#### 缩容过程

- 当⼀个节点被选中下线，它⾸先会被标记为不可调度，随后运⾏
  其上的pod将被疏散⾄其他节点。因为所有这些pod都属于ReplicaSet或
  者其他控制器，它们的替代pod会被创建并调度到其他剩下的节点（这
  就是为何正被下线的节点要先标记为不可调度的原因）

> 只有当Cluster Autoscaler知道节点上运⾏的pod能够重新调度到其他节
> 点，该节点才会被归还。

#### 设置节点调度策略

- kubectl cordon [node] 标记节点为不可调度（但对其上的pod不做任何事）。
- kubectl drain [node] 标记节点为不可调度，随后疏散其上所有pod。

> 两种情形下，在你⽤kubectl uncordon <node>解除节点的不可调度状态之前，不会有新pod被调度到该节点。

### 问题

#### 为何不能纵向扩展pod

- 纵向既给它们更多CPU和（或）内存，可以通过limits/requests 给予一定范围的缩阔，但是还是不算纵向扩展
- pod的资源请求是通过pod manifest的字段配置的，纵向伸缩pod需要通过改变这些字段来实现。现在暂无办法。

#### 如何确保一个节点在下线时不影响其内正在服务的pod

- 使用一个资源：podDisruptionBudget资源， 来指定下线等操作时需要保持的最少pod数量

- 使用 podDisruptionBudget
    - 创建pdb命令： `kubectl create pdb kubia-pdb --selector=app=kubia --min-available=3`

> 可以设置 maxUnavailable 来限制可以存在多少个不可用pod

```yaml
# pdb 基于 yaml创建
apiVersion: policy/v1beta1
kind: PodDisruptionBudget
metadata:
  name: kubia-pdb
spec:
  minAvailable: 2 # 可以用%30 来指定min-available
  selector:
    matchLabels:
      app: kubia
```

## pod的节点选择

### 节点容忍

- 配置节点污点，只有pod能够容忍这些污点，才能被分配到这个node上。
- 查看node的污点： `kubectl describe node node1` # 查看到 `Taints: <none>` ，没有配置污点
- 查看pod上污点容忍度： `kubectl describe pod pod-name` # 查看 `Tolerations: xxx`

#### Taint

- 格式：`<key>=<value>:<effect>`

> eg.: # value都是 null <br/>
> node.kubernetes.io/not-ready:NoExecute op=Exists for 300s  <br/>
> node.kubernetes.io/unreachable:NoExecute op=Exists for 300s <br/>

- 不同effect的效果
    - NoSchedule： 表⽰如果pod没有容忍这些污点，pod则不能被调度到包含这些污点的节点上
    - PreferNoSchedule： 尽量不要分配到该node，实在没有再分配
    - NoExecute：如果没有容忍该污点则不能运行pod，包括正在运行的pod

#### 实践

- 配置节点污点： `kubectl taint nodes node1 node-type=production:NoSchedule`
- 配置pod污点容忍度并部署

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prod
spec:
  replicas: 5
  selector:
    matchLabels:
      app: prod
  template:
    metadata:
      labels:
        app: prod
    spec:
      containers:
        - args:
            - sleep
            - "99999"
          image: busybox
          name: main
      tolerations:
        - key: node-type
          operator: Equal # 污点的value必须等于配置value才行
          value: production
          effect: NoSchedule
      #  tolerationSeconds: 3600 # 只有 NoExecute 才有效果，效果是如果不符合污点则可以等待多长时间后继续分配，默认300
```

### 节点亲缘性

#### 作用

- 比 node selector功能更多。
- 当调度某⼀个pod时，指定调度器可以优先考虑哪些节点。
- 可以查看 nodeAffinity、podAffinity、podAntiAffinity 下有哪些规则。
    - nodeAffinity: node 选择
    - podAffinity： pod亲和性选择
    - podAntiAffinity： pod调度时不会被分配到与不亲和的pod同样的node

#### 实践

- 给两个node配置lable
    - `kubectl label node node1 availability-zone=zone1 share-type=dedicated`
    - `kubectl label node node1 availability-zone=zone2 share-type=shared`
- 部署一个配置了节点亲缘性的pod

> DuringSchedulingIgnoredDuringExecution: 在调度时候并且不影响已经执行的pod; <br/>
> 效果是可以将pod调度优先到zone1里，多地部署时作用很大。 只有两个node时，会由一个被分到zone2，因为k8s的特性，尽量不然所有pod都在同个node里。

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pref
spec:
  replicas: 5
  selector:
    matchLabels:
      app: pref
  template:
    metadata:
      labels:
        app: pref
    spec:
      affinity:
        nodeAffinity:
          preferredDuringSchedulingIgnoredDuringExecution: # 优先级
            - weight: 80
              preference:
                matchExpressions:
                  - key: availability-zone
                    operator: In
                    values:
                      - zone1
            - weight: 20
              preference:
                matchExpressions:
                  - key: share-type
                    operator: In
                    values:
                      - dedicated
      containers:
        - args:
            - sleep
            - "99999"
          image: busybox
          name: main
```

- podAffinity的Deployment配置 [部分]

```yaml
...
affinity: # 尽量分配到与backend一个node
  podAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 80
        podAffinityTerm:
          topologyKey: kubernetes.io/hostname
          labelSelector:
            matchLabels:
              app: backend
...
```

- podAntiAffinity的Deployment配置 [部分]

```yaml
...
affinity: # 尽量不要分配到与frontend一个node
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution: # 如果想剩余没办法分配的pod也成功运行，可以用preferred。 required是强制，不能分配不分配。
    - topologyKey: kubernetes.io/hostname
      labelSelector:
        matchLabels:
          app: frontend
...
```

> 亲缘性调度是基于node label匹配的，所以要为每个node都配置好label才有效果。