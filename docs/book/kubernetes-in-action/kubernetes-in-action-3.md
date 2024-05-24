# Kubernetes-in-action (三)

---

> 本节内容：Service,Endpoint,Ingress 

## 服务

#### 作用

- 将请求路由到一组pod中的随机(可设置规则)一个pod
- 由于pod可能会重建或者有多个，所以需要有个统一的路由路口来让外部的服务知道该调用什么地址。(有点像nginx，路由转发)

#### 实践

- 创建一个多端口号，亲和性为clientIP的service
    - `kubectl exec pod-name -- curl -s http://service-addr` # 从pod内部执行一个命令， -- 命令结束后执行

```yaml
apiVersion: v1
kind: Service
metadata:
  name: kubia
spec:
  sessionAffinity: ClientIP # 设置亲和性，同一个clientIP的请求都会发到同一个pod. 只有 ClientIP 和 NONE 两种
  ports:
    - name: http
      port: 80
      targetPort: 8080
    - name: https
      port: 443
      targetPort: 8443
  selector:
    app: kubia
```

- 创建一个NodePort类型的服务，让外部系统可以访问集群内存服务

```yaml
apiVersion: v1
kind: Service
metadata:
  name: kubia-nodeport
spec:
  type: NodePort
  ports:
    - port: 80
      targetPort: 8080
      nodePort: 30123 # 可以用集群ip:30123 访问
  selector:
    app: kubia
```

- 创建一个LoadBalance类型的服务，让外部系统可以访问集群内部服务

```yaml
apiVersion: v1
kind: Service
metadata:
  name: kubia-loadbalancer
spec:
  type: LoadBalancer
  ports:
    - port: 80
      targetPort: 8080
  selector:
    app: kubia
```

#### Q&A

- 服务如何被client端pod发现
    - **可以用环境变量**：在pod创建时，会被初始化一系列的环境变量，其中就包含已存在的service地址. (
      KUBIA_SERVICE_HOST和KUBIA_SERVICE_PORT)
    - **使用全限定域名访问**：kubia.default.svc.cluster.local [service-name.namespace.type[svc,pod]
      .cluster-domain[默认=cluster.local]], 如果在相同的ns中，可以直接使用service name访问
        - `hostname --fqdn` pod 中执行，可查看上述名称(缩写： FQDN)
        - `kubectl -n kube-system edit configmap coredns` 查看里面host配置，或者kube的cluster 配置
        - `cat /etc/resolv.conf` 看pod的路由解析
        - 如果想使用其他cluster-domain，让某些pod走不同的dns，那需要把pod的dnsPolicy设置为 ClusterFirst
- 为什么要用LoadBalance而不是NodePort
    - 如果使用NodePort，并且指定node ip时，如果node挂了，那就不能访问了。
    - 使用LoadBalance时，会有一个额外ip，使用那个ip调用时，它会自动帮你把请求发给可用的node中service。
- LoadBalance会有什么问题
    - 如果多个节点时，可能需要多一跳来到达实际的pod。
    - 多次跳转后，clientIP可能不是真的客户端地址了，而是node地址或则其他。
- 如果想一次性获取所有可用的pod的地址怎么办
    - 创建headless service，既service的yaml中将spec.clusterIP设置为None,从而kube不会给他分配IP。
    - **直接连接headless服务时，是直接访问的是随机的一个pod，没有经过service的endpoint，而是从dns轮询中获取了ip直接访问了。**
    - 实践
        - 创建headless service
      ```yaml
      apiVersion: v1
      kind: Service
      metadata:
        name: kubia-headless
       #annotation:
        # service.alpha.kubernetes.io/tolerate-unready-endpoints: "true"
      spec:
        clusterIP: None
        ports:
        - port: 80
          targetPort: 8080
        selector:
          app: kubia
      ```
      - 查询kubia-headless的dns
        - 创建一个拥有nslookup工具的pod：`kubectl run dnsutils --image=tutum/dnsutils --generator=run-pod/v1 --command -- sleep infinity`
        - 查询dns解析结果： `kubectl exec dnsutils -- nslookup kubia-headless`
        - 发现返回的是后端pod的ip地址和FQDN
- 如果想一次性获取所有的pod的地址怎么办
    - 在headless
      service文件中的metadata.annotation字段加入：`service.alpha.kubernetes.io/tolerate-unready-endpoints: "true"`
    - 查看dns解析结果：`kubectl exec dnsutils -- nslookup kubia-headless`. 包含了未就绪的pod地址
- 如何使用headless service
  - 使用工具 `apt install dnsutils` -> `nslookup serviceName` -> 拿到pod地址，并访问
  - 使用headless的原因是为了通过service获取pod地址，而不是使用kube api server

## Endpoint

#### 作用

- service 通过 endpoint 资源和 pod 相连。 endpoint可以是集群外的地址，如果要访问外部系统。
- 没有指定pod的service是不会有endpoint资源产生，因为不知道路由给谁。
- 维护pod的iptables，以便分配流量

#### 实践

- 创建一个服务，指定externalName来指定pod，从而由kube自己创建出endpoint

```yaml
apiVersion: v1
kind: Service
metadata:
  name: external-service
spec:
  type: ExternalName
  externalName: api.somecompany.com #可以使用FQDN指定，常规可以用label指定
  ports:
    - port: 80
```

## Ingress

#### 作用

- 向外部系统提供集群内部pod服务。 (除NodePort和LoadBalance外的另一种方式)
- 可以配置不同的host以及不同的path走不同的service或者pod。 (host和path都是数组，可以配置多个)

#### 实践

- 创建一个ingress，并把ingress的`ip domain`配置在hosts文件中,这样可以用host直接访问

```yaml
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: kubia
spec:
  rules:
    - host: kubia.example.com
      http:
        paths:
          - path: /
            backend:
              serviceName: kubia-nodeport
              servicePort: 80
```

- 配置处理tls请求的ingress
    - 创建tls.key和tls.cert
        - `openssl genrsa -out tls.key 2048`
        - `openssl req -new -x509 -key tls.key -out tls.cert -days 360 -subj /CN=kubia.example.com`
    - 创建kube secret
        - `kubectl create secret tls tls-secret --cert=tls.cert --key=tls.key`
    - 创建ingress
    - 测试： `curl -k -v https://kubia.example.com`

```yaml
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: kubia
spec:
  tls:
    - hosts:
        - kubia.example.com
      secretName: tls-secret
  rules:
    - host: kubia.example.com
      http:
        paths:
          - path: /
            backend:
              serviceName: kubia-nodeport
              servicePort: 80
```

#### 运行原理

- 在client
  请求时，client会去查询kubia.example.com的ip地址，然后发送请求给ingress，ingress收到请求后会找path匹配的服务，从服务的endpoint中获取pod的地址，然后将请求转发给pod。

## 探针之就绪探针

#### 作用

- 使用后可以让未就绪的pod不被请求

#### 实践

- 在rc的yaml中添加就绪探针
    - 对现有pod不会有影响，需要重启pod才有效果，且探针是定时执行的，重启后需要等一会。
    - 给pod添加文件，让其就绪：`kubectl exec kubia-xxx -- touch /var/ready`

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
            - name: http
              containerPort: 8080
          readinessProbe: # 就绪探针
            exec:
              command: # 如果有该文件则表示就绪
                - ls
                - /var/ready 
```