# Kubernetes-in-action (八)

---

> 本节内容： kube 运行原理 & 安全防护 (service account, [cluster] role, [cluster] role binding,)

## 架构

### 组成

- kube控制平面
    - etcd分布式持久化存储
    - API服务器
        - 唯一与etcd交互的组件
        - 其他组件都与其交互，来获取需要的信息，或执行资源操作
        - 主要将资源变更同步到其他控制器，由他们来进行资源变更，自己则只是通知
    - 调度器
        - 控制pod的调度，默认是default-scheduler
    - 控制器管理器
        - 每种资源都有对应的控制器，控制器一直观察资源的状态是否与配置的一样，不一样则会请求api server去变更资源的状态以达到与配置一样。
        - 更新流程：控制器 -> api server -> kubectl
        - 控制器和kubectl之间是互不相关的，都由api server这个中心来控制
- 工作节点
    - Kubelet
        - 启动node后持续监控pod的资源状态并告诉api服务器
        - 接受api 服务器的更新指令来更新pod的状态
        - pod探针观测，并执行重启
    - Kubelet服务代理（kube-proxy）
        - 将工作节点的流量发到指定的pod，通过iptables实现将流量转发到pod上
    - 容器运⾏时（Docker、rkt或者其他）
- 附加组件
    - Kubernetes DNS服务器
        - 利用 api 服务器的监控机制来订阅service和endpoint的变动，以及dns记录的变更
        - 在更新间隙中，可能导致dns无效
    - 仪表板
    - Ingress控制器
        - 类似一个反向代理服务器
        - 虽然配置了service，但是流量不会通过service，而是直接连上pod，从而pod可以获取到源的client ip
    - Heapster（容器集群监控）
    - 容器⽹络接⼜插件（本章后⾯会做讨论

> `kubectl get events --watch` 是用来实时查看kubectl接收的事件

### pod 运行

- 每个pod在启动时，都会默认有一个基础容器(只执行暂停操作的容器)，用于处理pod内所有的容器公用一个linux命名空间。
- 如果基础容器被删除，则kubectl会重建它以及pod的所有容器。
- 例： 一个只声明nginx容器的pod， 生成pod时会有两个容器被创建

### kube的网络

- pod间的通讯实现
    - 没有时NAT(网络地址转换)来实现pod的通讯，为了简洁
    - 集群内部是一个局域网，所以可以通过ip地址直接访问(不同node)
    - 同node上：
        - 每个pod中基础容器会创建网络命名空间让pod内的所有容器都走同一个网络接口
        - pod会通过一个虚拟网络接口来连接到一个网桥： pod A -> veth pair -> bridge -> veth pair -> pod B

### service的实现

- service 无法被ping通，因为是个虚拟ip地址
- service相关的事情都是由kube-proxy进程处理，对于service和endpoint的变化，kube-proxy会更新到相应的iptables中，这样在一个请求在来后会被重定向到pod的地址。

## 安全防护

> kube 中由一系列的认证授权插件，在一个请求到达api服务器时，会经过这些插件，如果有一个通过则说明可以请求

### ServiceAccount

#### 作用

- 一种kube的资源
- 默认将service account配置的secret加载到pod中
- 每个ServiceAccount只能在自己的ns中使用

#### 实践

- 创建一个sa : sa-> service account 缩写，同样使用kubectl get sa等命令
- pod绑定这个sa
- 查看 sa是否可以拉取pod信息 (容器ambassador默认启动一个kube-proxy，所以可以访问api服务器)
    - `kubectl exec -it curl-custom-sa -c main curl localhost:8001/api/v1/pods`
- 检验pod的secret
    - `kubectl get sa -o yaml` # 查看 token secret 名称
    - `kubectl describe secret my-sa-token-tc54g` # 查看token，默认是jwt格式
    - `kubectl exec -it curl-custom-sa -c main -- cat /var/run/secrets/kubernetes.io/serviceaccount/token` #
      容器内挂载的token内容

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-sa
imagePullSecrets:
  - name: my-secret

---

apiVersion: v1
kind: Pod
metadata:
  name: curl-custom-sa
spec:
  serviceAccountName: my-sa
  containers:
    - name: main
      image: curlimages/curl:7.87.0
      command: [ "sleep", "9999999" ]
    - name: ambassador
      image: luksa/kubectl-proxy:1.6.2
```

### RBAC

#### 概念

- RBAC授权插件将⽤户⾓⾊作为决定⽤户能否执⾏操作的关键因素
- 由两组资源控制 (均可用kube get命令)
    - Role（⾓⾊）和ClusterRole（集群⾓⾊），它们指定了在资源上可以执⾏哪些动词
        - Role只能用于创建或者指定的ns
          - 可以用yaml文件或者命令(`kubectl create role service-reader --verb=get --verb=list --resource=services -n bar`)创建
    - RoleBinding （⾓⾊绑定） 和 ClusterRoleBinding （集群⾓⾊绑定），它们将上述⾓⾊绑定到特定的⽤户、组或ServiceAccounts上
        - RoleBinding：将role绑定到一个或多个 service account 或者 组、用户
          - 可以跨命名空间绑定service account
          - 命令： `kubectl create rolebinding test --role=service-reader --serviceaccount=foo:default -n foo`


#### 实践：Role，RoleBinding
- 创建两个ns： foo，bar
  - `kubectl create ns foo`, `kubectl create ns bar`
- 在两个空间中创建具有kube-proxy和curl工具的pod
  - `kubectl create -f curl-custom-sa.yaml -n bar`
  - `kubectl create -f curl-custom-sa.yaml -n foo`
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: curl-custom-sa
spec:
  serviceAccountName: default
  containers:
  - name: main
    image: curlimages/curl:7.87.0
    command: ["sleep", "9999999"]
  - name: ambassador
    image: luksa/kubectl-proxy:1.6.2
```
- 创建一个role，并给role赋予访问service的权限
  - `kubectl create -f role.yaml`
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: foo
  name: service-reader
rules:
  - apiGroups: [ "" ]
    verbs: [ "get", "list" ]
    resources: [ "services" ]
```
- 给role绑定 foo，bar两个空间default的serviceaccount
  - `kubectl create rolebinding test --role=service-reader --serviceaccount=foo:default -n foo`
  - `kubectl create rolebinding test2 --role=service-reader --serviceaccount=bar:default -n foo`
  - 
- 通过pod访问api server，查看是否具有访问权限
  - `kubectl exec -it curl-custom-sa -c main -n bar -- curl http://localhost:8001/api/v1/namespaces/foo/services`
  - `kubectl exec -it curl-custom-sa -c main -n foo -- curl http://localhost:8001/api/v1/namespaces/bar/services`
  
> RoleBinding可以在foo空间中声明, 但是可以将role 绑定到 bar空间的service account，因为role的声明是在foo中,
> 若是如此配置，则可以让bar空间的pod访问到foo空间的services （如上述实践）

> 由此得出： RoleBinding、Role都是和命名空间相关的，既这个命名空间的资源可以让谁访问，是这个空间内的谁还是其他的谁(角色)

#### 实践：ClusterRole，ClusterRoleBinding
> 有些资源不在命名空间中，所以需要用集群范围的角色定义。 如 pv、node、ns
> 集群资源只能用 ClusterRoleBinding 而不能用 RoleBinding

- 创建一个cluster role， 并赋予访问pv的权限. [不需要指定命名空间]
- 创建cluster role binding， 将role绑定到foo，bar的service account
  - ` kubectl create clusterrolebinding pv-test --clusterrole=pv-reader --serviceaccount=foo:default --serviceaccount=bar:default`
- 检查名称空间内的pod是否具有访问pv的权限
  - `kubectl exec -it curl-custom-sa -c main -n bar -- curl http://localhost:8001/api/v1/persistentvolumes`
  - `kubectl exec -it curl-custom-sa -c main -n foo -- curl http://localhost:8001/api/v1/persistentvolumes`

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: pv-reader
rules:
- apiGroups: [""]
  verbs: ["get", "list"]
  resources: ["persistentvolumes"]
```

#### 实践：ClusterRole，RoleBinding
> 使用RoleBinding结合ClusterRole： ClusterRole中配置资源范围只有RoleBinding所在的命名空间 <br/>
> 使用ClusterRoleBinding结合ClusterRole: ClusterRole中配置资源范围作用与整个集群。

- 在foo，bar中创建一个rolebinding，将clusterrole view (kube自带的) 绑定他们。
  - `kubectl create rolebinding view-test --clusterrole=view --serviceaccount=foo:default -n foo`
  - `kubectl create rolebinding view-test --clusterrole=view --serviceaccount=bar:default -n bar`
- 查看foo和bar中的pod是否可以查询命名空间内所有pod
  - `kubectl exec -it curl-custom-sa -c main -n foo -- curl http://localhost:8001/api/v1/namespaces/foo/pods`
  - `kubectl exec -it curl-custom-sa -c main -n bar -- curl http://localhost:8001/api/v1/namespaces/bar/pods`
- 查看foo和bar中的pod是否可以查询集群内所有pod
  - `kubectl exec -it curl-custom-sa -c main -n bar -- curl http://localhost:8001/api/v1/pods` # 失败， 403
- 删除foo中的role binding，添加一个cluster role binding，再次查看是否可以查询集群内的所有pod
  - `kubectl delete rolebinding view-test -n foo`
  - `kubectl create clusterrolebinding view-test --clusterrole=view --serviceaccount=foo:default`
  - `kubectl exec -it curl-custom-sa -c main -n foo -- curl http://localhost:8001/api/v1/pods` # 成功

> role、cluster role、role binding、 cluster role binding 之间的用法要多试试才能加深理解

- 从书中copy的
![从书中copy的](https://raw.githubusercontent.com/zhihui-Yu/images/main/kube-in-actions/C12-2.png)