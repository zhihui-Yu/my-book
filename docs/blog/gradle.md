# gradle

---

> 手册： https://docs.gradle.org/current/dsl/index.html

## 导入本地jar
```gradle
configure(project('project_dir_name')) {
    dependencies {
//        implementation files("${rootDir}/libs/xxx.jar") // 某个jar
        implementation fileTree("${rootDir}/libs") { include '*.jar' } // 目录下所有jar
    }
}
```


## gradle 命令
```shell
gradle init # 初始化一个gradle项目
gradle test # 执行名为test的task
.\gradlew run # 执行application的main方法
./gradlew build # 将程序以及所有依赖打包
 .\gradlew build --scan # 将打包的过程以及性能发布到gradle网站，方便查看与分析
```

## 基础知识
- 加载流程： settings.gradle -> build.gradle -> 子项目的 build.gradle 文件
- 单引号和双引号都可以表示字符串，但是有变量使用双引号，如 "print $var"
- 创建task：
    ```gradle
    tasks.register('task-name') {
        doLast {
            println 'task running'
        }
        doFirst {
        }
    }
    ```
- 设置project 变量
```shell
version = '1.0.0.GA' # 声明 project.version 值  
def javaVersion = '1.8' # 定义个untyped变量
```