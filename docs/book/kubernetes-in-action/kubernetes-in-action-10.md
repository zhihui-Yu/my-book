# Kubernetes-in-action (十)

--- 

> 本节内容：
> - 容器的资源限制，既requests，limits，LimitRange
> - CustomResourceDefinitions,自定义的资源配置

## requests & limits
- requests 不会超卖： 在创建pod时会判断node是否可以分配，不能则失败 
- limits 会超卖： 创建时不会判断，但是如果运行中超过了node最大的则会删除某些pod(按照pod的QoS等级)。

> 如果不设置requests，只有limits，则requests=limits <br/>
> 如果podA和podB的cpu资源request是 1：5， 则全力使用cpu时最大资源也是 1:5 <br/>
> pod OOMKill后会 10s, 20s, 30,... 300s 每隔一段时间重试，直到最后一直5min一次尝试重启

即使为pod设置了limits和requests，在容器内看见的cpu和memory的数量依旧是node级别的
- 在java应用种取系统的cpu数量来创建线程的，会让他创建出大量的线程并且每个线程会占用内存，而cpu实际只有一小部分：[如果我们使用的JDK版本支持这2个参数，那么我们只需要在运行Java程序时把这UseCGroupMemoryLimitForHeap参数加上，同时再给ActiveProcessorCount参数赋值实际分配给容器的cpu limit就可以了]
- 虽然限制了容器的核数，但并不意味着容器是在指定核上运行，在不同时间时，容器会在不同核上运行

Kubernetes将pod划分为3种QoS等级：
- BestEffort（优先级最低）： 没有配置limits和requests的pod， 资源不足第一个被杀死
- Burstable： ⾄少有⼀个容器只定义了requests但没有定义limits的pod，以及⼀个容器的requests和limits相等，但是另⼀个容器不指定requests或limits的pod
- Guaranteed（优先级最⾼）： CPU和内存都要设置requests和limits && 每个容器都需要设置资源量 && 每个容器的每种资源的requests和limits必须相等

### 创建一个配置requests和limits的pod
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: limited-pod
spec:
  containers:
  - image: busybox
    command: ["dd", "if=/dev/zero", "of=/dev/null"]
    name: main
    resources:
      requests:
        cpu: 200m
        memory: 10Mi
      limits:
        cpu: 1
        memory: 20Mi
```

## LimitRange

### 作用
- 配置资源类型（pod，pvc，container）对应的资源（cpu，memory）限制
- 只对LimitRange生成后的资源有作用
- **依旧可以通过创建多个pod来吃掉node的资源**

### 实践 
- 创建一个LimitRange在命名空间foo中: `kubectl create -f limits.yaml -n foo`
- 创建一个pod，并设置其requests.cpu=2 : `kubectl create -f limits-pod-too-big.yaml -n foo`
- 创建pod失败:
  - 显示：`The Pod "too-big" is invalid: spec.containers[0].resources.requests: Invalid value: "2": must be less than or equal to cpu limit`
  
> 如果不配置pod的resources，则默认是LimitRange中配置的

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: example
spec:
  limits:
  - type: Pod
    min:
      cpu: 50m
      memory: 5Mi
    max:
      cpu: 1
      memory: 1Gi
  - type: Container
    defaultRequest:
      cpu: 100m
      memory: 10Mi
    default:
      cpu: 200m
      memory: 100Mi
    min:
      cpu: 50m
      memory: 5Mi
    max:
      cpu: 1
      memory: 1Gi
    maxLimitRequestRatio: # limit最大为request的几倍
      cpu: 4
      memory: 10
  - type: PersistentVolumeClaim
    min:
      storage: 1Gi
    max:
      storage: 10Gi
```
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: too-big
spec:
  containers:
  - image: busybox
    args: ["sleep", "9999999"]
    name: main
    resources:
      requests:
        cpu: 2
```

## ResourceQuota

### 作用
- 限制命名空间中的可⽤资源总量

### 实践
- 创建一个 ResourceQuota 资源： `kubectl create -f quota-cpu-memory.yaml -n foo`
- 在没有LimitRange资源情况下创建pod：`kubectl create -f ../Chapter03/kubia-manual.yaml -n foo`
  - 显示ERROR: `Error from server (Forbidden): error when creating "../Chapter03/kubia-manual.yaml": pods "kubia-manual" is forbidden: failed quota: cpu-and-mem: must specify limits.cpu,limits.memory,requests.cpu,requests.memory`
```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: cpu-and-mem
spec:
  hard: # 命名空间下资源总量设置
    requests.cpu: 400m
    requests.memory: 200Mi
    limits.cpu: 600m
    limits.memory: 500Mi
    requests.storage: 500Gi # 可声明的总存储量
    ssd.storageclass.storage.k8s.io/requests.storage: 300Gi # ssd可申请量
    standard.storageclass.storage.k8s.io/requests.storage: 1Ti

    # 配置ns中资源最大数量
    pods: 10
    replicationcontrollers: 5
    secrets: 10
    configmaps: 10
    persistentvolumeclaims: 5
    services: 5
    services.loadbalancers: 1
    services.nodeports: 2
    ssd.storageclass.storage.k8s.io/persistentvolumeclaims: 2
```

> 由于我们创建了ResourceQuota，那么需要一个LimitRange，不然在创建pod时没有配置requests，limits的话 是没办法创建pod的。

LeastRequestedPriority: 优先将 pod调度到请求量少的节点上（也就是拥有更多未分配资源的节点）
MostRequestedPriority: 优先调度到请求量多的节点（拥有更少未分配资源的节点）, 使用场景：

- 为特定的pod状态或者QoS等级指定配额

> ⽬前配额作⽤范围共有4种： <br/>
> BestEffort: BestEffort QoS <br/>
> NotBestEffort : Burstable 和 Guaranteed QoS 的 pod <br/>
> Termination: 配置了 activeDeadlineSeconds 的pod <br/>
> NotTerminating:没有指定 activeDeadlineSeconds 的pod <br/>

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: besteffort-notterminating-pods
spec:
  scopes: # 最多创建4个属于BestEffort QoS并且没有配置activeDeadlineSeconds的pod
  - BestEffort
  - NotTerminating
  hard:
    pods: 4
```


## 自定义资源类型 (CustomResourceDefinitions)

### 作用
- 通过自定义资源类型，在apply后，kube环境中就可以通过声明该类型资源文件(yaml)来创建该类型资源。

### 样例
```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: websites.extensions.example.com
spec:
  scope: Namespaced
  group: extensions.example.com
  versions:
    - name: "v1"
      served: true
      storage: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              properties:
                gitRepo: 
                  type: string
  names:
    kind: Website
    # 名称的单数形式，作为命令行使用时和显示时的别名
    singular: website
    # 名称的复数形式，用于 URL：/apis/<组>/<版本>/<名称的复数形式>
    plural: websites
    # 允许你在命令行使用较短的字符串来匹配资源
    shortNames:
      - ws
```

```yaml
apiVersion: extensions.example.com/v1
kind: Website
metadata:
  name: kubia
spec:
  gitRepo: https://github.com/luksa/kubia-website-example.git
```