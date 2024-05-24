# Kubernetes-in-action (四)

---

> 本节内容： 卷，PV，PVC

## 卷

### 概述

- 让pod和宿主机共享一个空间，可以是文件，文件夹
- 多个pod可以共享同一个卷

### 卷类型

|                                类型                                                                                               |                  作用                  |
|:-------------------------------------------------------------------------------------------------------------------------------:|:------------------------------------:|
|                                                            emptyDir                                                             |            ⽤于存储临时数据的简单空⽬录            |
|                                                             gitRepo                                                             |          通过检出Git仓库的内容来初始化的卷          |
|                                                            hostPath                                                             |        ⽤于将⽬录从⼯作节点的⽂件系统挂载到pod中        |
|                                                               nfs                                                               |            挂载到pod中的NFS共享卷            |
|                                                  configMap、secret、downwardAPI                                                   |  ⽤于将Kubernetes部分资源和集群信息公开给pod的特殊类型的卷 |
|                                                      persistentVolumeClaim                                                      |         ⼀种使⽤预置或者动态配置的持久存储类型          |
| gcePersistentDisk （ Google ⾼ 效 能 型 存 储 磁 盘 卷 ） 、 <br/>awsElasticBlockStore（AmazonWeb服务弹性块存储卷）、<br/>azureDisk（MicrosoftAzure磁盘卷） |          ⽤于挂载云服务商提供的特定存储类型           |

#### emptyDir
- 实践
  - 创建fortune image到自己的docker repo，把yaml中的地址切换成自己的。 
    - fortune的[DockerFile](https://github.com/luksa/kubernetes-in-action/tree/master/Chapter06/fortune),创建镜像过程就不重复了。
  - 使用fortune隔一段时间就给html卷添加html文件
  - web-server读取文件
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: fortune
spec:
  containers:
  - image: luksa/fortune
    name: html-generator
    volumeMounts:
    - name: html
      mountPath: /var/htdocs
  - image: nginx:alpine
    name: web-server
    volumeMounts:
    - name: html
      mountPath: /usr/share/nginx/html
      readOnly: true
    ports:
    - containerPort: 80
      protocol: TCP
  volumes:
  - name: html
    emptyDir: {} # 默认使用kube的文件系统， 可以用过explain命令查看字段含义
```

- 注意
  - **在pod被删除时，emptyDir也会被删除**。 可以认为emptyDir是在把pod当成宿主机，pod里面的容器当初需要被挂在卷的东西。

#### gitRepo
- 实践
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: gitrepo-volume-pod
spec:
  containers:
  - image: nginx:alpine
    name: web-server
    volumeMounts:
    - name: html
      mountPath: /usr/share/nginx/html
      readOnly: true
    ports:
    - containerPort: 80
      protocol: TCP
  volumes:
  - name: html
    gitRepo:
      repository: https://github.com/luksa/kubia-website-example.git
      revision: master # 分支
      directory: . # . 代表根目录
```

- 注意
  - gitRepo也是一种emptyDir，所以容器删除时，卷也没有了。
  - 不支持私有库的拉去
  - 基本不用这种类型

#### hostPath
- 实践
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: mongodb 
spec:
  volumes:
  - name: mongodb-data
    hostPath:
      path: /tmp/mongodb
  containers:
  - image: mongo
    name: mongodb
    volumeMounts:
    - name: mongodb-data
      mountPath: /data/db
    ports:
    - containerPort: 27017
      protocol: TCP
```
- 注意
  - hostPath是将pod内的卷和node上卷相连接，所以pod删除了，重启后卷内数据还是在。
  - **如果在多node环境，pod重启后被分配到其他节点，那卷可能没有，所以数据也没有**。 用hostPath做全局数据备份时要考虑这点。

> nfs 和各个厂商的卷什么都大同小异，就是卷的类型不一样，和指定的参数不一样。 这些都可以用explain命令去了解

#### PV 和 PVC
- 概念
  - PV 是持久化卷，没有命名空间区分
  - PVC 是持久化卷申明，有命名空间区分
  - 使用过程：创建PV -> 创建PVC(绑定PV) -> pod中定义PVC。
  - 一个PV只能有一个PVC，在PVC删除后，PV会根据声明来决定时候格式化，如果是retain，那就是不删除却也不能被重新绑定。 
    - 可通过删除PV中的spec.claimRef，来让PV从Released变成Available。
  - 区分PV和PVC是为了解耦卷定义[类型，源]和卷声明[大小，读写]，并将卷声明从pod声明中抽出。
  - 访问模式 （节点非pod）
    - RWO——ReadWriteOnce——仅允许单个**节点**挂载读写。
    - ROX——ReadOnlyMany——允许多个**节点**挂载只读。
    - RWX——ReadWriteMany——允许多个**节点**挂载读写这个卷。
- 实践
  - 创建PV
  - 创建PVC
  - pod绑定PVC, 并在文件中添加数据。
  - 删除PVC
  - 重新创建PVC
  - 修改PV，删除旧的绑定源 -> `kubectl edit pv mongodb-pv`
  - 查看PV和PVC状态 -> pod又有旧数据了。
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: mongodb-pv
spec:
  capacity: 
    storage: 1Gi
  accessModes:
    - ReadWriteOnce
    - ReadOnlyMany
  persistentVolumeReclaimPolicy: Retain
  hostPath:
    path: /tmp/mongodb
```
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mongodb-pvc 
spec:
  resources:
    requests:
      storage: 1Gi
  accessModes:
  - ReadWriteOnce
  storageClassName: "" # 使用默认的storageClass，确保PVC绑定到预先配置的PV，而不是新创建的
```
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: mongodb
spec:
  volumes:
    - name: mongodb-data
      persistentVolumeClaim:
        claimName: mongodb-pvc
  containers:
    - image: mongo
      name: mongodb
      volumeMounts:
        - name: mongodb-data
          mountPath: /data/db
      ports:
        - containerPort: 27017
          protocol: TCP
```

> 注意： PV和PVC之间的关联是由kube的置备程序去选择的，但是PV和PVC的storageClass是一样的，这样就可以做一些分配规则。<br/>
>  pv 可以配置label， pvc可以配置matchLabels来选择pv

#### storageClass
- 概念
  - 存储类型，用于定义可用的存储类型
  - StorageClass资源指定当持久卷声明请求此StorageClass时应使⽤哪个置备程序来提供持久卷, 这样运维就不需要自己创建PV了
  - 可以用 `kubectl get sc` 来看本地有什么storageClass， 并可以使用`kubectl get sc sc-name -o yaml` 来显示其配置
- 实践
  - 配置一个storageClass
  - 运行一个pod指定PVC模板： 验证pod是否有存储卷
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: local
provisioner: rancher.io/local-path # 这是我云服务器自己的置备程序
reclaimPolicy: Retain # PV 回收策略  
volumeBindingMode: WaitForFirstConsumer # 在有pod绑定pvc时候，会自动创建pv
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: local-pvc
  annotations:
    volumeType: local
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: local-path
  resources:
    requests:
      storage: 128Mi
---
apiVersion: v1
kind: Pod
metadata:
  name: mongodb
spec:
  volumes:
    - name: mongodb-data
      persistentVolumeClaim:
        claimName: local-pvc
  containers:
    - image: mongo
      name: mongodb
      volumeMounts:
        - name: mongodb-data
          mountPath: /data/db
      ports:
        - containerPort: 27017
          protocol: TCP
```