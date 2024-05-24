# Kubernetes-in-action (九)

--- 

> 本节内容：pod的网络、内核功能、运行时用户配置

### 实践

#### 配置一个pod，让pod与node处于同一网络空间，既port也是共享
- 查看pod的网络 `kubectl exec pod-with-host-network -- ifconfig`
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-with-host-network
spec:
  hostNetwork: true # 使用主机的网络
  containers:
  - name: main
    image: alpine
    command: ["/bin/sleep", "999999"]
```

#### 使pod可以查询到主节点的PID 和 IPC命名空间
- `kubectl exec pod-with-host-pid-and-ipc -- ps aux`
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-with-host-pid-and-ipc
spec:
  hostPID: true
  hostIPC: true
  containers:
  - name: main
    image: alpine
    command: ["/bin/sleep", "999999"]
```

#### pod 在不指定运行用户时默认时root
> 这种情况不安全，所以在Dockerfile中使用USER来指定用户

- 启动容器 `kubectl run pod-with-defaults --image alpine --restart Never -- /bin/sleep 999999 pod/pod-with-defaults created`
- 查看id： `kubectl exec pod-with-defaults -- id`

#### 指定用户运行容器
- `kubectl exec pod-as-user-guest -- id`
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-as-user-guest
spec:
  containers:
  - name: main
    image: alpine
    command: ["/bin/sleep", "999999"]
    securityContext:
      runAsUser: 405 #用户的id，不是用户名，405对应guest
```

#### 以非root用户运行pod
- 运行时会显示失败，由于没办法当成root用户运行
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-run-as-non-root
spec:
  containers:
  - name: main
    image: alpine
    command: ["/bin/sleep", "999999"]
    securityContext:
      runAsNonRoot: true # 
```

#### 通过特权模式来运行一个pod
> /dev 目录是设备目录，关联硬件设备的
- 由于特权模式的/dev目录和非特权的是不一样的，所以验证这个就好了。 ``
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-privileged
spec:
  containers:
  - name: main
    image: alpine
    command: ["/bin/sleep", "999999"]
    securityContext:
      privileged: true # 特权模式
```

#### 为pod添加内核功能
> linux 内核功能默认以 CAP_开头，但是在pod中声明时可以不加前缀
- 修改(宿主机以及pod)系统时间：`kubectl exec -it pod-add-settime-capability -- date +%T -s "12:00:00"`
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-add-settime-capability
spec:
  containers:
  - name: main
    image: alpine
    command: ["/bin/sleep", "999999"]
    securityContext:
      capabilities:
        add:
        - SYS_TIME # 
```
#### 在容器中禁⽤内核功能
> 默认情况下容器拥有CAP_CHOWN权限， 允许进程修改⽂件系统中⽂件的所有者。
- 验证pod的默认权限
  - `kubectl exec pod-with-defaults chown guest /tmp`
  - `kubectl exec pod-with-defaults -- ls -la / | grep tmp`
- 禁用权限
  - `kubectl exec pod-drop-chown-capability -- chown guest /tmp` # 权限被禁用了
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-drop-chown-capability
spec:
  containers:
  - name: main
    image: alpine
    command: ["/bin/sleep", "999999"]
    securityContext:
      capabilities:
        drop:
        - CHOWN
```

#### 阻⽌对容器根⽂件系统的写⼊
- 在跟目录创建文件： `kubectl exec pod-with-readonly-filesystem -- touch /new-file` # 失败
- 在挂载目录上创建文件： `kubectl exec pod-with-readonly-filesystem -- touch /volume/newfile`
- 查看文件是否创建： `kubectl exec pod-with-readonly-filesystem -- ls -la /volume`
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-with-readonly-filesystem
spec:
  containers:
  - name: main
    image: alpine
    command: ["/bin/sleep", "999999"]
    securityContext:
      readOnlyRootFilesystem: true # 不允许对根文件系统写入
    volumeMounts:
    - name: my-volume
      mountPath: /volume
      readOnly: false # 允许挂载的存储卷可以被读写
  volumes:
  - name: my-volume
    emptyDir:
```

#### 在pod中为不同容器设置不同运行时用户，但可以共享存储卷
- 查看两个容器的id
  - `kubectl exec -it pod-with-shared-volume-fsgroup -c first -- id`
  - `kubectl exec -it pod-with-shared-volume-fsgroup -c second -- id`
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-with-shared-volume-fsgroup
spec:
  securityContext:
    fsGroup: 555
    supplementalGroups: [666, 777]
  containers:
  - name: first
    image: alpine
    command: ["/bin/sleep", "999999"]
    securityContext:
      runAsUser: 1111
    volumeMounts:
    - name: shared-volume
      mountPath: /volume
      readOnly: false
  - name: second
    image: alpine
    command: ["/bin/sleep", "999999"]
    securityContext:
      runAsUser: 2222
    volumeMounts:
    - name: shared-volume
      mountPath: /volume
      readOnly: false
  volumes:
  - name: shared-volume
    emptyDir:
```

#### 使用PodSecurityPolicy的前置配置
> 从 Kubernetes v1.21开始，Pod Security Policy 将被弃用，并将在 v1.25 中删除，Kubernetes 在 1.22 版本引入了 Pod Security Admission 作为其替代者。
> 如果要使用，需要api-server开启PodSecurityPolicy

#### 给不同的service account 分配不同权限
> 默认PodSecurityPolicy 是不生效的，需要手动配置
- 创建一个私有的psp（如下yaml）
- 创建clusterrole： `kubectl create clusterrole psp-default --verb=use --resource=podsecuritypolicies --resource-name=default`
- 创建clusterrolebinding: `kubectl create clusterrolebinding psp-all-users --clusterrole=psp-default --group=system:authenticated --serviceaccount=foo:default`
- 测试效果

```yaml
apiVersion: extensions/v1beta1
kind: PodSecurityPolicy
metadata:
  name: default
spec:
  privileged: true
  runAsUser:
    rule: RunAsAny
  fsGroup:
    rule: RunAsAny
  supplementalGroups:
    rule: RunAsAny
  seLinux:
    rule: RunAsAny
  volumes:
  - '*'
```

#### 阻⽌了pod使⽤宿主节点的PID、IPC、⽹络命名空间，运⾏特权模式的容器，以及绑定⼤多数宿主节点的端⼜（除11 000～11 000和13 000～14 000范围内的端口）
- 运行完这个yaml后，集群中不能再部署使⽤宿主节点的PID、IPC、⽹络命名空间的pod了

```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: default
spec:
  hostIPC: false # 不能使用宿主机的IPC
  hostPID: false # 不能使用宿主机的PID
  hostNetwork: false # 不能使用宿主机的网络空间
  hostPorts: # 只能使用宿主机中固定的端口
  - min: 10000
    max: 11000
  - min: 13000
    max: 14000
  privileged: false # 不能特权模式运行
  readOnlyRootFilesystem: true # 容器根目录只读
  runAsUser: # 可以用任意用户运行容器
    rule: RunAsAny
  fsGroup:
    rule: RunAsAny
  supplementalGroups:
    rule: RunAsAny
  seLinux: # 可以使用任意的SELinux选项， SELinux 安全选项
    rule: RunAsAny
  volumes: # 可以用所有类型的存储卷
  - '*'
```

> `kubectl get psp`  # psp -> PodSecurityPolicy

#### 基于上个案例，实现固定用户ID运行容器
> 如果是Dockerfile 中指定的USER，在运行yaml时候会被覆写成2.
```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: default
spec:
  hostIPC: false
  hostPID: false
  hostNetwork: false
  hostPorts:
  - min: 10000
    max: 11000
  - min: 13000
    max: 14000
  privileged: false
  readOnlyRootFilesystem: true
  runAsUser: # 指定用户ID
    rule: MustRunAs
    ranges:
    - min: 2
      max: 2
  fsGroup:
    rule: MustRunAs
    ranges:
    - min: 2
      max: 10
    - min: 20
      max: 30
  supplementalGroups:
    rule: MustRunAs
    ranges:
    - min: 2
      max: 10
    - min: 20
      max: 30
  seLinux:
    rule: RunAsAny
  volumes:
  - '*'
```

#### 配置允许、默认添加、禁⽌使⽤的内核功能
```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: default
spec:
  allowedCapabilities: # 允许添加的
  - SYS_TIME
  defaultAddCapabilities: # 默认添加的
  - CHOWN
  requiredDropCapabilities: # 不允许的操作
  - SYS_ADMIN
  - SYS_MODULE
  hostIPC: false
  hostPID: false
  hostNetwork: false
  hostPorts:
  - min: 10000
    max: 11000
  - min: 13000
    max: 14000
  privileged: false
  readOnlyRootFilesystem: true
  runAsUser:
    rule: RunAsAny
  fsGroup:
    rule: RunAsAny
  supplementalGroups:
    rule: RunAsAny
  seLinux:
    rule: RunAsAny
  volumes:
  - '*'
```

#### 限制pod可以使⽤的存储卷类型
```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: default
spec:
  runAsUser:
    rule: RunAsAny
  fsGroup:
    rule: RunAsAny
  supplementalGroups:
    rule: RunAsAny
  seLinux:
    rule: RunAsAny
  volumes: # 允许的存储卷类型
  - emptyDir
  - configMap
  - secret
  - downwardAPI
  - persistentVolumeClaim
```

#### Network policy： 阻⽌任何其他ns的客户端访问
```yaml
kind: NetworkPolicy
metadata:
  name: default-deny
spec:
  podSelector: # 空的则是匹配所有
```

#### Network policy：指定连接
> NetworkPolicy允许具有app=webserver标签的pod访问具有app=database的pod的访问，并且仅限访问5432端⼜
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: postgres-netpolicy
spec:
  podSelector:
    matchLabels:
      app: database
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: webserver
    ports:
    - port: 5432
```

#### Network policy：指定cidr
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ipblock-netpolicy
spec:
  podSelector:
    matchLabels:
      app: shopping-cart
  ingress:
  - from:
    - ipBlock:
        cidr: 192.168.1.0/24
```

#### Network policy：限制出口流量
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: egress-net-policy
spec:
  podSelector:
    matchLabels:
      app: webserver
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - port: 5432
```