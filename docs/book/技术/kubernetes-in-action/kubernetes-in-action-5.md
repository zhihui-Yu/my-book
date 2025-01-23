# Kubernetes-in-action (五)

---

> 本节内容： configmap, secret

### 参数化运行容器
#### 作用
- 支持在运行docker container时候添加参数
- 就像启动MySQL container时候，可以设置MYSQL_ROOT_PASSWORD环境变量来改变mysql的root用户密码

#### 参数化方式
- Dockerfile中指定ENTRYPOINT和CMD
- 创建容器时添加参数： `docker run <image> <args>`

#### ENTRYPOINT 之 shell 和 exec 形式的区别
- shell形式 —— 如ENTRYPOINT node app.js。
  - shell会多运行一个shell程序
- exec形式 —— 如ENTRYPOINT[＂node＂,＂app.js＂]

#### 实践
- 创建镜像
  - 使用[地址](https://github.com/luksa/kubernetes-in-action/tree/master/Chapter07/fortune-args)创建一个image
- 运行镜像
  - 使用`docker run -it image-name`运行镜像 -> 查看输出
  - 或者使用 `docker run -it image-name 5` -> 查看输出

### 参数化运行pod
#### 作用
- 在容器运行是设定一下参数，如mysql的密码
- 可以配置容器的环境变量，以达到某种效果

#### 实践
- 在pod的yaml中配置容器的参数
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: fortune2s
spec:
  containers:
  - image: luksa/fortune:args
    args: ["2"] # 配置启动时传入的参数, 也可以用 多行 '-' 来配置
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
    emptyDir: {}
```
- 配置容器的环境变量
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: fortune-env
spec:
  containers:
  - image: luksa/fortune:env
    env: # 配置环境变量， k-v形式的数组
    - name: INTERVAL
      value: "30"
    - name: SECOND_VAR
      value: "$(INTERVAL)-time" # 值为 "30-time", 可以引用定义的环境变量
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
    emptyDir: {}
```

### ConfigMap
#### 作用
- 将需要配置的东西抽象出来，pod只需要引用configMap，而不需要关心具体的值。

#### 实践
- 查看configmap: `kubectl get configmap [name -o yaml #输出成yaml]`
- 删除configmap: `kubectl delete configmap name`
- 使用yaml文件创建configmap: `kubectl create -f  configmap.yaml`
- 指定KV以创建configmap: `kubectl create configmap myconfigmap --from-literal=foo=bar --from-literal=bar=baz`
- 使用配置文件创建configmap: 
  - `kubectl create configmap my-config --from-file=ssl.conf` #文件名为K，内容为V，文件名有效才能建
  - `kubectl create configmap my-config --from-file=key=ssl.conf` # 可以指定key
- 使用文件夹创建configmap：`kubectl create configmap my-config --from-file=configmap-files` #文件名为K，内容为V，文件名有效才能建
- 将configmap的value传递给pod
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: fortune-env-from-configmap
spec:
  containers:
  - image: luksa/fortune:env
    env:
    - name: INTERVAL # 环境变量名
      valueFrom: # 使用这个字段来定义值的来源
        configMapKeyRef:
          optional: true # 可以设置为optional，否则有configmap才会启动容器
          name: fortune-config 
          key: sleep-interval
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
    emptyDir: {}
```
- 将多个环境变量的值传入容器
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: fortune-env-from-configmap
spec:
  containers:
  - image: luksa/fortune:env
    envFrom: # 使用这个字段声明多个env需要导入
    - prefix: CONFIG_ # 所有的key导入后都添加这个前缀
      configMapRef:
        name: my-config-map # 从map中导入
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
    emptyDir: {}
```
- 让configmap的值在容器启动变量上生效
  - 初始化值到环境变量，在启动参数上引用环境变量
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: fortune-args-from-configmap
spec:
  containers:
  - image: luksa/fortune:args
    env:
    - name: INTERVAL
      valueFrom: 
        configMapKeyRef:
          name: fortune-config
          key: sleep-interval
    args: ["$(INTERVAL)"] # 使用环境变量
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
    emptyDir: {}
```
- 将值为文件内容的configmap挂载到容器内
  - 测试
    - `kubectl port-forward fortune-configmap-volume 8080:80 &`
    - `curl -H "Accept-Encoding: gzip" -I localhost:8080` # 有开启gzip则成功
    - `kubectl exec fortune-configmap-volume -c web-server -- ls /etc/nginx/conf.d` # 查看挂载文件
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: fortune-configmap-volume
spec:
  containers:
  - image: luksa/fortune:env
    env:
    - name: INTERVAL
      valueFrom:
        configMapKeyRef:
          name: my-config
          key: sleep-interval
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
    - name: config
      mountPath: /etc/nginx/conf.d # 挂在文件到这个目录
      # subPath: myconfig.conf # 使用subPath会让文件挂载时只影响当前文件，而不会影响其他。 不用则会导致文件夹下只有这个文件
      readOnly: true
    - name: config
      mountPath: /tmp/whole-fortune-config-volume
      readOnly: true
    ports:
      - containerPort: 80
        name: http
        protocol: TCP
  volumes:
  - name: html
    emptyDir: {}
  - name: config
    configMap:
      name: my-config
      defaultMode: 0660 # configmap默认权限是 644，通过配置defaultMode来修改其权限
      items: # 定义哪些key被使用
      - key: my-nginx-config.conf # key 名称
        path: gzip.conf # value 存储的文件名
```
> configmap 在被更新后会同步文件到pod，但是如果pod不支持重载，那只有新的pod会生效。 <br/>
> 同步并不是同步的，所有会不一致的情况。<br/>
> 用items时候不能用subPath<br/>
> 使用subPath挂载时不能接收configMap的更新


### Secret
#### 作用
- 作为一种kube资源，存储敏感的数据，以KV键值存储。
- secret存储在内存中，而不是磁盘。
- 每个pod都会被挂载一个default-token-xx的secret，作为访问kube api-server的凭证，如果在需要访问api-server时。
- secret limit 1M

#### 实践
- 将secret挂载到容器内的目录
  - 创建一个secret: `kubectl create secret generic fortune-https --from-file=https.key --from-file=https.cert --from-file=foo` #生成https所需的key，cert，以前有教程
  - 创建一个configmap：`kubectl create configmap ssl-configmap-2 --from-file=ssl.conf --from-literal=sleep-interval=10`
  - 创建pod
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: fortune-https
spec:
  containers:
  - image: luksa/fortune:env
    name: html-generator
    env:
    - name: INTERVAL
      valueFrom:
        configMapKeyRef:
          name: ssl-configmap # 从configmap中获取环境变量，key则是configmap中的key名称
          key: sleep-interval
    volumeMounts:
    - name: html
      mountPath: /var/htdocs
  - image: nginx:alpine
    name: web-server
    volumeMounts:
    - name: html
      mountPath: /usr/share/nginx/html
      readOnly: true
    - name: config
      mountPath: /etc/nginx/conf.d
      readOnly: true
    - name: certs
      mountPath: /etc/nginx/certs/
      readOnly: true
    ports:
    - containerPort: 80
    - containerPort: 443
  volumes:
    - name: html
      emptyDir: {}
    - name: config
      configMap:
        name: ssl-configmap #挂载configmap
        items:
          - key: ssl.conf #configmap中的key
            path: https.conf
    - name: certs
      secret:
        secretName: fortune-https #挂载secret
```
  - 测试pod
    - `kubectl port-forward fortune-https 8443:443 &` # 将容器端口放出
    - `curl https://localhost:8443 -k -v` # 在kube中直接访问容器，查看连接握手。

- 使用secret设置dockerhub账号来拉取私有镜像
  - 创建dockerhub账号的secret: `kubectl create secret docker-registry dockerhub-secret --docker-username=myname --docker-password=mypassword --docker-email=my.email@example.com`
  - 在pod的yaml中配置拉取镜像时的secret
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: private-pod
spec:
  imagePullSecrets:
  - name: dockerhub-secret
  containers:
  - image: username/private-image:tag
    name: main
```

- 使用secret设置环境变量 <font color=red> 不建议使用，不安全</font>
  - 配置pod yaml中的env值
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: private-pod
spec:
  imagePullSecrets:
  - name: dockerhub-secret
  containers:
  - image: username/private-image:tag
    name: main
    env:
    - name: INTERVAL # 环境变量名称
      valueFrom:
        secretKeyRef:
          name: test-secret
          key: sleep-interval
```
  