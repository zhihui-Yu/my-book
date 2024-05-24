# 深入浅出Java多线程

---

`date: 2021-07-28`

> 图书在线观看地址: https://redspider.gitbook.io/concurrent/

## 基础篇：

- 一个进程是一个程序，一个进程可以有多个线程，每个进程占用的内存是相互隔离的，线程则共享进程下所有内存。
- Java多线程实现方式： Thread, Runnable, Callable,Future,FutureTask
- 线程有自己所属的线程组 `Thread.currentThread().getThreadGroup().getName()` ， 默认创建线程的优先级是5， 越低优先级越高。
- 线程的状态包含 [NEW,RUNNABLE, BLOCKED,WAITING,TIMED_WAITING,TERMINATED].
    - Thread.interrupt() - [让线程中断]
    - Thread.interrupted() - [让线程变成中断，再调用一次就变成不中断]
    - Thread.isInterrupted() - [只判断是不是中断]
- 让线程串行执行需要用到锁。使用 notify/ notifyAll 来唤醒其他线程，wait 让当前线程等待。 可以使用 Semaphore 或者
  volatile来当作一个乐观锁。
- 管道
    - 管道是基于"管道流"的通信方式。JDK提供了PipedWriter、 PipedReader、 PipedOutputStream、
      PipedInputStream。其中，前面两个是基于字符的，后面两个是基于字节流的。
    - 可以用管道流方式实现线程之间的通讯，传输文件。
- Object
    - sleep: 释放cpu不释放锁， wait会释放锁。
    - join: 线程进入等待态，等join的这个线程执行完成后，再继续执行当前线程。
- ThreadLocal
    - 它为每个线程都创建一个副本，每个线程可以访问自己内部的副本变量。内部是一个弱引用的Map来维护。
    - InheritableThreadLocal 类与 ThreadLocal 类稍有不同，Inheritable是继承的意思。它不仅仅是当前线程可以存取副本值，而且它的子线程也可以存取这个副本值。

## 原理篇：

- 线程在读取内存变量后，会在自己的缓冲区复制一份，这也就导致了一致性问题。
    - Java 运行时内存模型： 程序序计数器、本地方法栈、虚拟机栈、堆、方法区
    - JMM [Java 内存模型]：线程内存，线程本地内存，主存。
- 系统执行指令时，可能出于某些原因而对其进行重排序，一般有三种情况： 编译器优化重排，指令并行重排，内存系统重排。
    - 重排有时会导致系统出现问题。
    - JMM 提供一种 happens-before 的原则来控制并发情况下的重排问题。
- volatile 是Java 提供来使变量禁止指令重排以及内存可见性的关键字。
    - 禁止指令重排是通过内存屏障实现的。
    - 当变量在内存中被更改了，马上会让其他线程持有的副本失效，从而实现内存拿到的都是最新，但并不是线程安全的，经常使用其当作乐观锁。

- synchronize 在静态方法[类，静态变量]上时，锁类，在实例方法[对象，变量]上时锁实例。 也可以时synchronize(o.class[o])来使用。
    - 锁有无锁状态, 偏向锁状态, 轻量级锁状态, 重量级锁状态. 根据锁的竞争情况来升级，在STW(stop the world)
      时，会查看有无需要降级的锁，有则进行降级。

- CAS[compare and swap] 乐观锁，用于读多写少的场景。 读少写多的场景用悲观锁，避免长期重试消耗资源。
    + CAS 使用 Unsafe 类实现，该类由C++实现，在linux中是使用 cmpxchgl 实现的。
    + CAS 缺点：
        * ABA问题 -> 加入版本号[AtomicStampedReference实现，在变量前加版本号或者时间戳]
        * 长时间获取不到锁，自旋消耗cpu。
        * 只能对变量进行操作 -> 使用 AtomicReference 或者使用 锁。

- AQS[AbstractQueuedSynchronizer] -> 一个FIFO的双端队列来维护所有线程的Node。有很多类都是基于这个实现的，如重入锁，公平锁，门闩锁等待。
    - 获取锁一般使用自旋的cas锁。

## JDK工具篇：

### 线程池原理以及创建过程：

#### 构造参数：

- **int corePoolSize**：该线程池中核心线程数最大值
    - 核心线程：线程池中有两类线程，核心线程和非核心线程。核心线程默认情况下会一直存在于线程池中，即使这个核心线程什么都不干（铁饭碗），而非核心线程如果长时间的闲置，就会被销毁（临时工）。
- **int maximumPoolSize**：该线程池中线程总数最大值 。
    - 该值等于核心线程数量 + 非核心线程数量。
- **long keepAliveTime**：非核心线程闲置超时时长。
    - 非核心线程如果处于闲置状态超过该值，就会被销毁。如果设置allowCoreThreadTimeOut(true)，则会也作用于核心线程。
- **TimeUnit unit**：keepAliveTime的单位。
    - TimeUnit是一个枚举类型 ，包括以下属性：
        - NANOSECONDS ： 1微毫秒 = 1微秒 / 1000 MICROSECONDS ： 1微秒 = 1毫秒 / 1000 MILLISECONDS ： 1毫秒 = 1秒 /1000
          SECONDS ： 秒
        - MINUTES ： 分 HOURS ： 小时 DAYS ： 天
- **BlockingQueue workQueue**：阻塞队列，维护着等待执行的Runnable任务对象。
    - 常用的几个阻塞队列：
        - LinkedBlockingQueue 链式阻塞队列，底层数据结构是链表，默认大小是Integer.MAX_VALUE，也可以指定大小。
        - ArrayBlockingQueue 数组阻塞队列，底层数据结构是数组，需要指定队列的大小。
        - SynchronousQueue 同步队列，内部容量为0，每个put操作必须等待一个take操作，反之亦然。
        - DelayQueue 延迟队列，该队列中的元素只有当其指定的延迟时间到了，才能够从队列中获取到该元素 。
- **ThreadFactory factory**
    - 创建线程的工厂 ，用于批量创建线程，统一在创建线程时设置一些参数，如是否守护线程、线程的优先级等。如果不指定，会新建一个默认的线程工厂。
- **RejectedExecutionHandler handler**
    - 拒绝处理策略，线程数量大于最大线程数就会采用拒绝处理策略，四种拒绝处理的策略为 ：
        - ThreadPoolExecutor.AbortPolicy：默认拒绝处理策略，丢弃任务并抛出RejectedExecutionException异常。
        - ThreadPoolExecutor.DiscardPolicy：丢弃新来的任务，但是不抛出异常。
        - ThreadPoolExecutor.DiscardOldestPolicy：丢弃队列头部（最旧的）的任务，然后重新尝试执行程序（如果再次失败，重复此过程）。
        - ThreadPoolExecutor.CallerRunsPolicy：由调用线程处理该任务。

#### 线程池类型：

- newCachedThreadPool - 当线程不用会回收
- newFixedThreadPool - 没有任务非核心线程也不会回收
- newSingleThreadExecutor - 单核心线程执行
- newScheduledThreadPool - 定时任务执行

> 阿里Java手册建议，创建线程池还是使用 ThreadPoolExecutor 方式去创建比较好，更了解自己需要的情况。 <br/>
> 注意：线程池队列最大就是 Integer.MAX, 超过会报错了。

#### 阻塞队列： BlockingQueue

- 实现类有 ArrayBlockingQueue， LinkedBlockingQueue， DelayQueue， PriorityBlockingQueue，SynchronousQueue。
    - 原理： 通过自旋锁竞争，然后插入，如果已满就可能要阻塞插入。 取出也是一样，需要获取锁，并且队列有数据，才能获取到，否则会阻塞。
    - 场景： 在线程池的等待队列经常用到，已经生产消费者模式也用到。

### 锁

- synchronize 无法重入，所以引入了 ReentrantLock
    + ReentrantReadWriteLock，在读多写少的环境下使用 StampedLock 性能更高，且解决ABA问题和线程饥饿问题。
    + 锁实现相关类AbstractQueuedSynchronizer、AbstractQueuedLongSynchronizer、AbstractOwnableSynchronizer、Condition、Lock、ReadWriteLock

### 并发集合：

- Map: ConcurrentHashMap， ConcurrentNavigableMap (这个接口提供了针对给定搜索目标返回最接近匹配项的导航方法)，
- ConcurrentSkipListMap
- Queue: ConcurrentLinkedDeque, ConcurrentLinkedQueue
- Set: ConcurrentSkipListSet (用ConcurrentSkipListMap实现)， guava里面的 ConcurrentHashSet。

> 基本都是用 CAS 锁实现，但是不同集合有他自己的实现。

#### CopyOnWrite，

- 写时复制思想的体现。 在读多写少的情况下很不错。 实现类： CopyOnWriteArrayList， 其他实现的CopyOnWriteMap
    - 原理：(利用重入锁保证并发) 在写的时候，复制一份出来，在复制的容器上添加新的值。然后用新的替换旧的。 缺点： 容器大时候，非常消耗内存。

### 线程通讯工具

- Semaphore 限制线程的数量
    - 原理： 内部维护一个 int 值， 来限制线程请求次数，重写了 AQS 的 tryAcquireShared 方法， 也有公平和非公平实现。
    - 场景： 现在执行方法的线程数量
- Exchanger 两个线程交换数据
    - 原理：A 发送消息后，B接收到后调用 exchange()方法做出回应后，A才不会阻塞。 据说是用ConcurrentHashMap 实现的。
    - 场景：两两线程需要互传消息，A等待B的结果。 可以设置等待超时时间。
- CountDownLatch 线程等待直到计数器减为0时开始工作 (门闩，屏障)
    - 原理： 内部实现一个继承 AQS 的 Sync 类， 没有刷新门闩 count 的机制，所以只能用一次
    - 场景： 游戏前置加载，当所有异步加载完成后，正式开始游戏。
- CyclicBarrier 作用跟CountDownLatch类似，但是可以重复使用
    - 原理： ReentrantLock + Condition 实现的等待/通知模式。 如果有一个线程被broken了，其他也会收到影响。 broken-->(
      在reset时候，还是有其他等待线程)
    - 场景： 不同游戏关卡的加载，通过reset() 来实现。
- Phaser 增强的CyclicBarrier
    - 原理： 内部使用了两个基于Fork-Join框架的原子类辅助
    - 场景： 修改修改 count 的数量情况下。
- fork-join 框架： jdk提供的一种基于工作结果窃取算法的分而治之思想的框架。 将一个任务分为多个任务，让其他线程去完成后，由自己合并结果。
  > 一般使用都是 ForkJoinTask 子类 RecursiveAction(无返回值的ForkJoinTask) 或者 RecursiveTask(有返回值的ForkJoinTask)
- 原理： 内部自定义了一个结果 WorkQueue (双端队列，所有结果都在里面， LIFO)，ForkJoinPool中的每个工作线程都维护着一个工作队列
- 场景： see FibonacciTest
- Stream 使用： Stream.of(), 流式计算写法更加间接了，但是内部实现原理也包裹的更好了。
- 多线程并行计算原理： 最后使用 ReduceTask -> AbstractTask -> CountedCompleter -> ForkJoinTask， 使用了 fork-join 框架来实现。
- ScheduledThreadPoolExecutor 重复运行一个任务或者执行延迟任务。
  > 在此之前使用 Timer，由于单线程，如果运行一个出错了，其他的任务也将不会在执行。


