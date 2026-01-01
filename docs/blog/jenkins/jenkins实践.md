## docker + jenkins + github + springboot application 的 CI/CD

> 本文以centos 8 的阿里云 云服务器 为案例。
>
> 云服务需要开放8080给jenkins用，以及一个springboot服务的端口。

### 一、docker 安装

1. 删除原先docker 如果有想重装的话：

   - 查看docker的版本 
   
      ```
      yum list installed | grep docker
      ```
      ![image-20210530152008035](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530152008035.png)

   - 删除相关文件：

     ```
     yum -y remove containerd.io.x86_64 docker-ce-cli.x86_64 docker-scan-plugin.x86_64 # 列表内的删除
     ```
     
    - 清理文件: 
   
	  ```
        yum clean all
      ```
   
    > 这里用docker search 时就会告诉你docker没有了。
   
2. 安装docker
   - 安装docker 基础包

     ```
     yum install -y yum-utils device-mapper-persistent-data lvm2
     ```
     ![image-20210530154259933](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530154259933.png)

   - 设置稳定仓库

     ```
     yum-config-manager \
         --add-repo \
         https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo
     ```

     ![image-20210530154437753](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530154437753.png)

   - 安装最新版本(latest)
     ```
     yum install docker-ce docker-ce-cli containerd.io
     ```
     > 最后complete 就是可以了。
     > 也可以自定义版本 ： 
     >
     > yum list docker-ce --showduplicates | sort -r  #查看版本
     > sudo yum install docker-ce-<VERSION_STRING> docker-ce-cli-<VERSION_STRING> containerd.io #安装指定版本

   - 配置镜像源(一般用阿里云或者清华之类的)：
     
     ```
     vi  /etc/docker/daemon.json
     ```
     
     将下面的粘贴进去就好了：
     
     ```
     {
         "registry-mirrors": ["https://pee6w651.mirror.aliyuncs.com"]
     }
     ```
   
   - 启动docker
     
     ```
     systemctl start docker
     ```

     > 如果pull很慢可以重启一下，还不行就换一个源试一下。
     
### 二、docker中安装jenkins

1. 下载maven (用于挂载到jenkins 内)

   ```shell
   # 下载资源
   
   wget http://mirrors.cnnic.cn/apache/maven/maven-3/3.3.9/binaries/apache-maven-3.3.9-bin.tar.gz
   
   # 解压
   
   tar vxf apache-maven-3.3.9-bin.tar.gz
   
   # 移到一个目录
   
   mv apache-maven-3.3.9 /opt/maven-3.3.9
   
   # 配置环境变量
   
   export MAVEN_HOME=/opt/maven-3.3.9
   export PATH=${PATH}:${MAVEN_HOME}/bin
   
   # 刷新文件
   
   source /etc/profile
   
   # 查看版本号，有显示则配置成功
   
   mvn -v  
   ```

2. 安装jenkins+启动容器

   ```shell
   docker run \
     -u root \
     --rm \
     -d \
     -p 8080:8080 \
     -p 50000:50000 \
     -v /var/jenkins_home:/var/jenkins_home \
     -v /usr/lib/jvm/:/usr/lib/jvm/ \
     -v /opt/data/:/opt/data/ \
     -v /opt/maven-3.3.9:/opt/maven-3.3.9 \
     -v /var/run/docker.sock:/var/run/docker.sock \
     --name jenkins \
     jenkinsci/blueocean
   ```

3. 查看容器是否运行

   ![image-20210530164437165](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530164437165.png)

### 三、jenkins 配置

1. 进去jenkins 并安装插件

   > 连接为 http://ip:8080

   然后会看见这样的图：

   <img src="https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530165156634.png" alt="image-20210530165156634" style="zoom: 80%;" />

   在宿主机中运行一下命令获取密码：

   ```shell
   cat /var/jenkins_home/secrets/initialAdminPassword
   ```

   ![image-20210530165242599](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530165242599.png)

   粘贴密码进去然后安装默认的插件：

   ![image-20210530165544609](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530165544609.png)

   设置账户(要记住账户密码即可，邮箱必填，但可以填不存在的)：
   ![image-20210530165814666](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530165814666.png)

   下一步：

   ![image-20210530170001707](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530170001707.png)

   ![image-20210530170024069](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530170024069.png)

2. 重启后进去jenkins并配置jenkins

   填写刚才写的amin账户并登入：

   ![image-20210530170121636](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530170121636.png)

    进来后看见这个算是安装Jenkins成功了

   ![image-20210530170204311](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530170204311.png)

   为部署程序先配置jenkins:

   1. 下载plugin

      ![image-20210530170733176](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530170733176.png)

      找到这些插件并点击下载后重启

      ![image-20210530170913794](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530170913794.png)

   2. 全局配置

      再次进去jenkins并设置全局配置

      ![image-20210530171133257](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530171133257.png)

      查看容器内的jdk位置

      ![image-20210530171456549](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530171456549.png)

      配置jdk

      ![image-20210530171528190](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530171528190.png)

      git 默认就好

      ![image-20210530171614218](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530171614218.png)

       配置maven

      ![image-20210530171724583](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530171724583.png)

      配置docker，先点apply再点save.

      ![image-20210530171858490](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530171858490.png)

      

   3. 系统配置

      ![image-20210530172033657](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530172033657.png)

      配置github， 点击GitHub 下面的 advance后会显示如下

      ![image-20210530172843519](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530172843519.png)

      在github中配置webhook

      ![image-20210530173431890](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530173431890.png)

      apply加save保存配置。

### 四、部署springboot application

1. 创建一个maven的item

   ![image-20210530173638712](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530173638712.png)

   进入后填完名称选maven后点ok

   ![image-20210530173724746](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530173724746.png)

   

2. 配置过程

   配置github url

   ![image-20210530173929362](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530173929362.png)

   ![image-20210530174036388](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530174036388.png)

   ![image-20210530174216980](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530174216980.png)

   添加完保存后，在选择刚才创建的方式

   ![image-20210530174255497](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530174255497.png)

   添加webhook的支持

   ![image-20210530174408501](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530174408501.png)

   在build前需要做一些配置

   ![image-20210530210550575](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530210550575.png)

   配置build之后要做的事情：

   在配置这个之前，先配置build目录在宿主机（容器内也可以）：

   ```shell
   cd /opt/data
   mkdir build
   chmod 755 build
   cd build
   vi Dockerfile
   chmod 755 Dockerfile # 在编译保存后运行
   ```

   将下面内容粘贴到文件中(注意jar的名称配置)：

   ```
   #java1.8基础镜像
   FROM java:8  
   #创建/tmp目录并持久化到Docker数据文件夹，因为Spring Boot使用的内嵌Tomcat容器默认使用/tmp作为工作目录          
   VOLUME /tmp            
   #复制jar到test下且重命名为test_web0.jar
   ADD jenkins-test-1.0-SNAPSHOT.jar web.jar 
   #容器开放端口
   EXPOSE 80            
   ENTRYPOINT ["java","-jar","web.jar"]
   ```

   > 这里注意jar的名称要和自己打包后的一致

   ```shell
   #将打包好的jar项目，移到/opt/data/build目录
   mv /var/jenkins_home/workspace/application-test/target/jenkins-test-1.0-SNAPSHOT.jar /opt/data/build
   #切换目录到/opt/data/build
   cd /opt/data/build
   #执行构建Dockerfile命令
   docker build -t demo:v1.0 .
   #停止之前的容器运行
   docker stop demo
   #删除之前的容器
   docker rm demo 
   #运行刚刚创建的容器
   docker run -d --name demo -p 8081:8081 demo:v1.0
   echo "构建完成"
   ```

   ![image-20210530203053404](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530203053404.png)

   最后apply save一下。

   build试一下：

   ![image-20210530205817396](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530205817396.png)

   

   > 如果报错
   >
   > 1. 容器缺少 git，则安装一下git就好。
   >
   > 2. 如果build 的步骤有问题，看一下是不是文件名配置有问题，修改一下。
   >
   > 3. 如果时stop容器出问题，可以运行下面命令创建一个容器，然后再重新build 一下。
   >
   >    docker run -d --name demo -p 8081:8081 demo:v1.0

   

     

### 五、测试

1. 访问ip:port 测试效果：

   ![image-20210530210931655](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530210931655.png)

2. 修改代码，查看会不会自动build。 是成功的。

​     ![image-20210530211230521](https://raw.githubusercontent.com/zhihui-Yu/images/main/jenkins/image-20210530211230521.png)

如果不行，回到上面配置webhook地方再配置一下就可以了。



> ps: 如果有什么问题我们可以一起讨论一下。 欢迎指教。