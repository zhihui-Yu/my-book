# Kubernetes In Action

--- 

`date: 2023-03-19`

## 资源列表

| resource name                  | usage                                 | note                  | doc                                                     |
|:-------------------------------|:--------------------------------------|:----------------------|:--------------------------------------------------------|
| Pod                            | 实际应用run的地方，由至少一个容器组成                  | 如果容器内进程启动失败，pod资源仍然存在 | [Kubernetes-in-action (一)](kubernetes-in-action-1.md)   |
| ReplicaSet                     | 管理pod，弹性伸缩                            | 只关心pod的数量，不关心pod的状态   | [Kubernetes-in-action (二)](kubernetes-in-action-2.md)   |
| Role/ClusterRole               | 创建角色并设置角色拥有的权限                        |                       | [Kubernetes-in-action (二)](kubernetes-in-action-2.md)   |
| Jobs                           | 任务 ：完成临时任务后销毁pod                      |                       | [Kubernetes-in-action (二)](kubernetes-in-action-2.md)   |
| CronJobs                       | 定时任务：完成后销毁                            |                       | [Kubernetes-in-action (二)](kubernetes-in-action-2.md)   |
| DaemonSet                      | 守护进程集 ：它不关心副本数量，只关心为每个符合的node都要建一个pod |                       | [Kubernetes-in-action (二)](kubernetes-in-action-2.md)   |
| Service                        | 将请求路由到一组pod中的随机(可设置规则)一个pod           |                       | [Kubernetes-in-action (三)](kubernetes-in-action-3.md)   |
| Endpoint                       | service 通过 endpoint 资源和 pod 相连        |                       | [Kubernetes-in-action (三)](kubernetes-in-action-3.md)   |
| Ingress                        | 将内部服务对外开放                             |                       | [Kubernetes-in-action (三)](kubernetes-in-action-3.md)   |
| persistentVolume               | 数据卷资源                                 |                       | [Kubernetes-in-action (四)](kubernetes-in-action-4.md)   |
| persistentVolumeClaim          | 数据卷声明资源，与PV/storeclass连用              |                       | [Kubernetes-in-action (四)](kubernetes-in-action-4.md)   |
| storageClass                   | 配置数据卷类型的资源                            |                       | [Kubernetes-in-action (四)](kubernetes-in-action-4.md)   |
| Secret                         | 存储私密信息的资源                             |                       | [Kubernetes-in-action (五)](kubernetes-in-action-5.md)   |
| ConfigMap                      | 存储一些pod会用的配置信息资源                      |                       | [Kubernetes-in-action (五)](kubernetes-in-action-5.md)   |
| downward api                   | 让容器获取pod的信息                           |                       | [Kubernetes-in-action (六)](kubernetes-in-action-6.md)   |
| kube api-server                | 存储了集群信息, 各种资源类型可定义的api version        |                       | [Kubernetes-in-action (六)](kubernetes-in-action-6.md)   |
| Deployment                     | 管理pod，会创建rs资源来管理pod                   |                       | [Kubernetes-in-action (七)](kubernetes-in-action-7.md)   |
| StatefulSet                    | 配置由状态的pod                             |                       | [Kubernetes-in-action (七)](kubernetes-in-action-7.md)   |
| Node                           | 集群节点资源                                |                       |                                                         |
| RoleBinding/ClusterRoleBinding | 将角色绑定到某个serviceAmount                 |                       | [Kubernetes-in-action (八)](kubernetes-in-action-8.md)   |
| ServiceAccount                 | 配置集群中名称空间的用户                          |                       | [Kubernetes-in-action (八)](kubernetes-in-action-8.md)   |
| LimitRange                     | 配置集群中资源定义的限制                          |                       | [Kubernetes-in-action (十)](kubernetes-in-action-10.md)  |
| ResourceQuota                  | 限制命名空间中的可⽤资源总量                        |                       | [Kubernetes-in-action (十)](kubernetes-in-action-10.md)  |
| CustomResourceDefinitions      | 自定义资源类型                               |                       | [Kubernetes-in-action (十)](kubernetes-in-action-10.md)  |
| CustomResourceDefinition       | 创建自定义的resource                        |                       | [Kubernetes-in-action (十)](kubernetes-in-action-10.md)  |
| HorizontalpodAutoscaler        | pod⽔平扩容器                              |                       | [Kubernetes-in-action (十一)](kubernetes-in-action-11.md) |


## 场景应用

### 场景1：希望 Client Pod 在 Server Pod 后面启动

- 做法1： 在client-pod中配置init container去调用 server pod, 直到 server pod启动。

```yaml
# client yaml
apiVersion: v1
kind: Pod
metadata:
  name: fortune-client
spec:
  initContainers:
    - name: init
      image: busybox
      command:
    - sh
    - -c
    - 'while true; do echo "Waiting for fortune service to come up..."; wget http://fortune -q -T 1 -O /dev/null >/dev/null 2>/dev/null && break; sleep 1; done; echo "Service is up! Starting main container."'
  containers:
    - image: busybox
      name: main
      command:
    - sh
    - -c
    - 'echo "Main container started. Reading fortune very 10 seconds."; while true; do echo "-------------"; wget -q -O - http://fortune; sleep 10; done'
```

- 做法2：使用钩子来检测 server pod是否启动，如果没有则等待。
    - 启动后（Post-start）钩⼦：在钩子运行完成前pod会一直处于 Pending，如果钩子失败会导致主容器运行失败
    - 停⽌前（Pre-stop）钩⼦：在应用停止前执行，不论是否成功都会关闭容器

> 钩子是针对容器而不是pod, 由于很难看见钩子的运行日志，所以可以将container的dir挂载到pod的dir，将日志输入其中。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-with-prestop-hook
spec:
  containers:
    - image: luksa/kubia
      name: kubia
      ports:
        - containerPort: 8080
          protocol: TCP
      lifecycle:
        postStart:
          exec:
            command:
              - sh
              - -c
              - "echo 'hook will fail with exit code 15'; sleep 5 ; exit 15"
        preStop:
          httpGet:
            port: 8080
            path: shutdown
```

> pod关闭流程：执⾏停⽌前钩⼦ -> 向容器的主进程发送SIGTERM信号 -> 等待容器优雅地关闭或者等待终⽌宽限期超时 ->
> 如果容器主进程没有优雅地关闭，使⽤SIGKILL信号强制终⽌进. <br/>
> 终 ⽌ 宽 限 期 可 以 通 过 pod spec 中 的 spec.terminationGracePeriodPeriods字段来设置

### 场景2：如何正常处理pod关闭/启动是的流量

- Pod 更新过程

![pod 删除时发⽣的⼀连串事件](https://raw.githubusercontent.com/zhihui-Yu/images/main/kube-in-actions/C17-1.png)

![pod 删除时事件发⽣的时间线](https://raw.githubusercontent.com/zhihui-Yu/images/main/kube-in-actions/C17-1.png)

- 做法：
    - 添加就绪探针，让容器在没有真的ready前不接收请求
    - 添加钩子让容器不会立即关闭，让容器有时间管理连接
    - 尽量在kube-proxy更新更新iptabls后关闭程序 [各种问题可能导致关闭程序在更新iptables之前，连接就会失败]

## kube的管理

### 建议

- 构建的容器镜像尽可能小，这样pull会快
- 合理地给镜像打标签，正确地使⽤ImagePullPolicy: 如果pod意外重启了，并且使用了latest镜像，这可能不是你想要的
- 使⽤多维度⽽不是单维度的标签 && 通过注解描述每个资源： 让使用人员对资源的归属和场景更清晰
- 给进程终⽌提供更多的信息：以为终止并且没有错误信息是很痛苦的
- 处理日志信息：将容器的日志信息存储node的某个path，这样会让你在找错误时更有帮助 | 使用ELK/EFK等监控工具亦可