# JVM 核心技术

## JAVA 前言

- JDK (Java Development Kit) = JRE + 开发工具
- JRE(Java Runtime Environment) = JVM (Java Virtual Machine) + 类库
- 一次编译，到处执行的原理： java字节码可以在有JVM的环境中运行，不关心操作系统的版本，减少了调试不同环境兼容性的工作。

## 系统指标

- 业务需求指标：如吞吐量(QPS、TPS)、响应时间(RT)、并发数、业务成功率等。
- 资源约束指标：如 CPU、内存、I/O 等资源的消耗情况。

## 字节码

如何读懂字节码

```txt
    javap -c HelloWorld.class -- 反编译
    javap -c verbose HelloWorld.class -- 输出附加信息

    案例一： 
    #1 = Methodref #4.#13 // java/lang/Object."<init>":()V
    
    含义： 
        #1 常量编号, 该文件中其他地方可以引用。
        = 等号就是分隔符.
        Methodref 表明这个常量指向的是一个方法；具体是哪个类的哪个方法呢? 类指向的 #4, 方法签名指向的 
        #13; 当然双斜线注释后面已经解析出来可读性比较好的说明了。
    
    案例二： 
    public static void main(java.lang.String[]);
    descriptor: ([Ljava/lang/String;)V
    flags: ACC_PUBLIC, ACC_STATIC
    Code:
      stack=2, locals=2, args_size=1

    含义：
        ([Ljava/lang/String;)V ： 其中小括号内是入参信息/形参信息；左方括号表述数组；L 表示对象；后面的java/lang/String就是类名称；小括号后面的 V 则表示这个方法的返回值是 void；
        flags: ACC_PUBLIC, ACC_STATIC ： 表示 public 和 static
        stack=2, locals=2, args_size=1 ： 执行该方法时需要的栈(stack)深度是多少，需要在局部变量表中保留多少个槽位, 还有方法的参数个数

    注意： 无参构造函数的参数个数是1， 因为this也要占一个位置。

    案例三：
    初始化对象三部曲：
    初始化对象
    - new 占三位，创建对象
    - dup 复制栈顶引用值
    - invokespecial 执行对象初始化

    astore {N} or astore_{N} – 赋值给局部变量，其中 {N} 是局部变量表中的位置。
    iconst_{N} 用来将常量值N加载到栈里面
    istore_{N} 将变量存储到在 LocalVariableTable 的槽位 N 中。
    dstore 4 将 double 值保存到本地变量4号槽位
    putfield – 将值赋给实例字段
    putstatic – 将值赋给静态字段
    swap 指令用来交换栈顶两个元素的值
    pop 指令则从栈中删除最顶部的值。
    dup 指令复制栈顶元素的值。
    dup_x1 将复制栈顶元素的值，并在栈顶插入两次
    dup2_x1 则复制栈顶两个元素的值，并插入第三个值
```

## 类加载器

- 一个类在 JVM 里的生命周期有 7个阶段，分别是加载(Loading)、验证(Verification)、准备(Preparation)、解析(Resolution)、初始化(
  Initialization)、使用(Using)、卸载(
  Unloading)。

- JVM自带的类加载器 (使用双亲委托机制加载类)
    - 启动类加载器（BootstrapClassLoader）- 加载 Java 的核心类，代码打印为null
    - 扩展类加载器（ExtClassLoader）- 加载 JRE 的扩展目录，代码打印为null
    - 应用类加载器（AppClassLoader）- 加载系统属性指定的 jar 包和类路径

- 自定义类加载器
    - 继承ClassLoader 类，覆写方法来实现自定义加载器。

## Java 内存模型

- JVM 内存结构可分为 线程栈 + 堆内存 + 堆外内存。
- JVM 堆由 heap + non-heap组成， heap由 yong[Eden, Survivor] + old 组成, non-heap 由 Metaspace + CCS(存放 class 信息的) +
  Code Cache (
  存放 JIT 编译器编译后的本地机器代码) 组成
- 由于线程的工作时会去主内存拷贝一份成员变量副本回工作空间，所以就有了内存可见性问题。解决如下
    - synchronized 会让变量回主内存取值
    - volatile 保证内存可见性，使用读写屏障禁止cpu指令重排序，更新缓存时，标记主存的值已经失效，通知其他副本更新。

注意： 有些人测试时发现没有生效，可能由于使用了println(),或者多个线程执行很快，thread1改完，thread2才读。

![hotspot运行时数据区.png](https://raw.githubusercontent.com/zhihui-Yu/images/main/java/hotspot%E8%BF%90%E8%A1%8C%E6%97%B6%E6%95%B0%E6%8D%AE%E5%8C%BA.png)
## JVM 启动参数

```html
-Duser.timezone=GMT+08  // 设置用户的时区为东八区
-Dfile.encoding=UTF-8      // 设置默认的文件编码为UTF-8
java -XshowSettings:properties -version # 查看默认的所有系统属性
java -XshowSettings:vm -version # 查看 VM 设置
java -XshowSettings:locale -version # 查看当前 JDK/JRE 的默认显示语言设置
mvn package -Djava.test.skip=true / mvn package -DskipTests # 不执行单元测试
-Xmx4g, 指定最大堆内存为4g，一般为70%~80%的系统可用内存
-Xms4g, 指定堆内存空间的初始大小为4g
-Xss1m, 设置每个线程栈的字节数为1MB，与-XX:ThreadStackSize=1m等价
-verbose:gc 在 GC 日志中输出详细的GC信息，可动态开关
-XX:+PrintGCDetails 和 -XX:+PrintGCTimeStamps：打印 GC 细节与发生时间, 使用Xlog:gc* 代替
-Xloggc:file：与-verbose:gc功能类似，只是将每次 GC 事件的相关情况记录到一个文件中
-XX:+UseG1GC：使用 G1 垃圾回收器
-XX:+UseConcMarkSweepGC：使用 CMS 垃圾回收器
-XX:+UseSerialGC：使用串行垃圾回收器
-XX:+UseParallelGC：使用并行垃圾回收器
-XX:+HeapDumpOnOutOfMemoryError 产生oom自动dump堆内存
-XX:HeapDumpPath 指定dump文件目录
-XX:OnError="shell" 发现致命异常时，执行一个shell
-XX:OnOutOfMemoryError 抛出 OutOfMemoryError 错误时执行的脚本
-XX:ErrorFile=filename 致命错误的日志文件名，绝对路径或者相对路径。
```

```shell
javac GCTest.java # 编译
java -Xss200k -verbose:gc -Xmx5m -Xms1m -Xlog:gc* -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath="C:\work\java-base\src" -XX:+TraceJNIHandleAllocation GCTest # 执行命令 且加入参数
```

可以使用 https://www.eclipse.org/mat/ 内存分析工具来看内存泄漏问题

### Java Debug 工具

| tool name | info |
|:----------|:-----|
|   javac     | JDK 内置的编译工具   |
|javap |    反编译 class 文件的工具|
|javadoc|    根据 Java 代码和标准注释，自动生成相关的 API 说明文档|
|jps| 展示 Java 进程信息（列表）|
|jstat| 用来监控 JVM 内置的各种统计信息，主要是内存和 GC 相关的信息。|
|jmap |主要用来 Dump 堆内存|
|jcmd |本地诊断工具，只支持连接本机上同一个用户空间下的 JVM 进程|
|jstack| 打印出 Java 线程的调用栈信息.一般用来查看存在哪些线程，诊断是否存在死锁等。|
|jinfo |查看具体生效的配置信息以及系统属性，还支持动态增加一部分参数。|
|jrunscript 和 jjs| 执行脚本.都是 JDK 8 自带的 JavaScript 引擎 Nashorn|
|jconsole| 可以从多个维度和时间范围去监控一个 Java 进程的内外部指标。进而通过这些指标数据来分析判断 JVM 的状态，为我们的调优提供依据。|
|jvisualvm| 效果同上，但是可以加插件|
|JDWP |全称是 Java Debug Wire Protocol，中文翻译为“Java 调试连接协议”，是用于规范调试器（Debugger）与目标 JVM 之间通信的协议。|
|jdb |启用了 JDWP 之后，可以使用各种客户端来进行调试/远程调试。|

> 特殊手法： 定义MBean, 通过修改MBean的成员变量来修改程序的行为

### GC 算法

- 引用计数：每个对象有自己的被引用的计数，为0时会被统一清理
- 标记清除算法（Mark and Sweep）
    - 过程中需要暂停系统（stop the world）来做可达性分析
    - 由于Mark之后需要整理内存碎片，防止碎片过多导致内存不可分配
    - 为了让整理碎片时间更短，引出了分代概念，将heap分为了 young (eden[有多个 线程本地分配缓冲区 TLAB] + s0 + s1) + old
- 标记整理
    - 由于标记清除后，内存会有很多段空白，可能导致一个有很多空间，但是放不下一个大对象。
      由此引入整理，在清除后，将所有的数据整理到一块，这样就空出了一个连续的空间可以分配对象
- 标记复制
    - 标记对象后，将存活对象复制到新的空间，然后清除旧的。 优点是可以同时进行标记和复制，缺点是需要额外的空间。

### 垃圾收集器
- 串行 GC（Serial GC）
    - 串行 GC 对年轻代使用 mark-copy（标记—复制）算法，对老年代使用 mark-sweep-compact（标记—清除—整理）算法。
    - 该选项只适合几百 MB 堆内存的 JVM，而且是单核 CPU 时比较有用。
- 并行 GC（Parallel GC）
    - 在年轻代使用“标记—复制（mark-copy）算法”，在老年代使用“标记—清除—整理（mark-sweep-compact）算法”
    - 在执行“标记和复制/整理”阶段时都使用多个线程
    - 并行垃圾收集器适用于多核服务器，主要目标是增加吞吐量 （清理速度加快，多线程导致停顿久一点点）
- CMS 垃圾收集器
    - 对年轻代采用并行 STW 方式的 mark-copy（标记—复制）算法，对老年代主要使用并发 mark-sweep（标记—清除）算法。
    - 不对老年代进行整理，使用空闲列表（free-lists）来管理内存空间的回收
    -  mark-and-sweep（标记—清除）阶段没有STW，但是仍有CPU抢占。
    - 如果服务器是多核 CPU，并且主要调优目标是降低 GC 停顿导致的系统延迟，那么使用 CMS 是个很明智的选择。
    - 流程： Initial Mark（初始标记, 会STW） -> Concurrent Mark（并发标记, 同步骤一一起运行） -> Concurrent Preclean（并发预清理）-> Concurrent Abortable Preclean（可取消的并发预清理）-> Final Remark（最终标记, 第二次STW）-> Concurrent Sweep（并发清除）-> Concurrent Reset（并发重置, 为下次GC做数据初始化）
    - 老年代不会碎片整理，可能有问题
- G1 垃圾收集器
    - 垃圾最多的小块会被优先收集。这也是 G1 名称的由来。
    - 尽可能满足配置的停顿时间处理垃圾回收， -XX:+UseG1GC -XX:MaxGCPauseMillis=50
    - 堆不再分成年轻代和老年代，而是划分为多个（通常是 2048 个）可以存放对象的小块堆区域， 这些小块可能属于eden，survivor，old
    - G1 适合大内存，需要较低延迟的场景。
    - 步骤： Initial Mark（初始标记）-> Root Region Scan（Root 区扫描）-> Concurrent Mark（并发标记）-> Remark（再次标记, 会STW） -> Cleanup（清理）
    - 转移暂停：混合模式（Evacuation Pause(mixed)）： 清理后会开始整合对象，标记整理一样。
    - Remembered Sets（历史记忆集）简介: 每个小块都有一些自身引用的记忆，用于并发标记
- ZGC 垃圾收集器
    - 通过染色指针和读屏障来标记和清理垃圾，期间也有STW，但由于工作量很小，所以都很快，并且扫描都是并发的，只有在mark的一些阶段会STW， 延迟在10ms以内。
    - 步骤： 暂停—标记开始阶段（STW）[标记根对象集合指向的对象] -> 并发标记/重映射阶段 [遍历对象图结构，标记对象] -> 暂停—标记结束阶段(STW)[同步点，弱根对象清理] -> 并发准备重定位阶段 [引用处理、弱对象清理等] -> 暂停—重定位开始阶段 (STW) [根对象指向重定向集合] -> 并发重定位阶段 [重定向集合中的对象重定向]
    - 染色指针标记对象：Marked0、Marked1、Remapped、Finalizable
- Shenandoah GC
    - 早于ZGC，与ZGC定位类似。
    - 步骤：初始标记阶段 STW -> 并发标记阶段 -> 最终标记阶段 STW -> 并发清理阶段 -> 并发转移阶段 -> 初始引用更新阶段 STW -> 并发引用更新阶段 -> 最终引用更新阶段 STW -> 并发清理阶段
      GC 内存治理由大到小，阶段由简入繁。
> 延迟: 一次请求的往返延迟 <br/>
> 吞吐量: 一般指相当一段时间内测量出来的系统单位时间处理的任务数或事务数

Oracle GraalVM:  是 Oracle 开源的一款通用虚拟机产品，官方称之为 Universal GraalVM，是新一代的通用多语言高性能虚拟机。能执行各类高性能与互操作性任务，在无需额外开销的前提下允许用户构建多语言应用程序。
- 可以为多种语言提供编译服务，并且有较大的执行性能提升。

### 实践
- GC 分析工具
    - [GCEasy](https://gceasy.io/)
    - [FastThread](https://fastthread.io/)
    - [HeapHero](https://heaphero.io/)
    - [GCViwer](https://github.com/chewiebug/GCViewer) -> 开源
    - [BTrace](https://github.com/btraceio/btrace/) -> 问题追踪
    - [Arthas](https://github.com/alibaba/arthas) -> 问题追踪 + 性能分析

- Thread 分析
    - 创建过程： Thread.start() -> JVM Thread 对象创建 -> OS 系统的 Thread 创建 -> JVM 线程栈内存分配 -> 启动 Thread.run() -> 销毁JVM对象同时销毁OS Thread
    - 所以的Thread对象在JVM中都由一个Threads_list管理
    - JVM线程状态：_thread_new[初始化的新线程] -> _thread_in_Java[正在执行 Java 代码的线程] -> _thread_in_vm[JVM 内部执行的线程] -> _thread_blocked[由于某种原因被阻塞的线程,获取锁、等待条件、休眠、执行阻塞的 I/O 操作]
    - threadA.join() 让执行代码的线程等ThreadA执行完毕再继续
    - Java Synchronization 是由操作系统提供的管程(Monitor)实现的。管程有锁定、解锁两种状态，可以用来实现线程的同步访问。 在java 对象头上会存储对象的锁标志(2bit，00,01,10,11)来确定锁的类型，无锁 -> 偏向-> 轻量-> 重量
    - 自旋锁：在争取锁时，失败后先自旋一会，没准就获取到了，但是也可能浪费cpu。 适应性自旋：根据上次自旋次数来决定当前自旋次数。
    - http://fastthread.io/ 使用FastThread 来分析dump下来的Thread日志，有图形界面，更加直观。
    - GC的工作线程一般是总CPU*5/8，实际核心数 < 系统检测到的, 会导致频繁的切换上下文而性能降低

- JVM 内存分析
    - 对象头占用8字节（64位在没有开启指针压缩时也是8，否则时12字节，但是实际时16字节，8的倍数）
    - JVM遵循对齐，按照8的倍数分配内存
    - int 4字节，char 1字节，对象头占用8字节。 在申请空间时由大到小排序，先分配大的，在分配小的
    - MAT 全称是 Eclipse Memory Analyzer Tools。 用于分析内存泄露
    - errors 分析:
        - OutOfMemoryError: Java heap space -> 加大内存，代码调优
        - OutOfMemoryError: GC overhead limit exceeded -> GC无法回收垃圾，内存也满了。最好进行代码优化
        - OutOfMemoryError: PermGen space -> 永久代空间满了,加大内存或者JVM参数调优
        - OutOfMemoryError: Metaspace -> 元空间满了，方法如上
        - OutOfMemoryError: Unable to create new native thread -> 无法创建更多线程，MAT内存分析，优化代码
        - OutOfMemoryError: Out of swap space -> 系统物理内存分配不足，系统调优+代码优化
        - OutOfMemoryError: Requested array size exceeds VM limit -> 分配空间超过JVM允许范围，代码检查是否存在问题
        - OutOfMemoryError: Kill process or sacrifice child ->  内存超分配导致内存不足然后按评分(高)杀死进程，OOM killer 调优 / 加大内存
    - 影响GC的因素
        - 高分配速率（High Allocation Rate）-> eden区单位时间内创建对象很多会导致频繁的回收对象。
        - 过早提升（Premature Promotion） -> 大量对象由于频繁Young-GC而升迁到老年代，从而导致老年代频繁GC
        - 对象检查越多，暂停时间越长，导致GC越慢
    - 引用类型对GC的影响
        - Weak(弱)：如果只有弱引用对象关联到当前对象，GC可以强制回收。
        - Soft(软)：由GC自己决定，一般内存不足时才会回收
        - Phantom(虚)：只有手动调用clear方法才会被回收
> 内存溢出: 正常原因导致内存不足<br/>
> 内存泄露: 没用的对象太多并且没有被回收导致内存不足

### 案例分析
- 背景
    - 启动参数：`-Xmx4g -Xms4g -XX:+UseG1GC -XX:MaxGCPauseMillis=50`
    - 由于设置暂停时间50ms，运行一段时间后发现暂停时间飙升到1.5s
- 步骤
    - 查询日志，观察gc时间，yong和old
    - 查看gc日志，dump 日志
    - 发现有48个gc工作线程，但是实际cpu只有4核8g
- 原因
    - k8s 环境没隔离好，导致pod使用node的核心数来创建线程，但是实际只有4核，在多线程间频繁上下文切换导致耗时增加