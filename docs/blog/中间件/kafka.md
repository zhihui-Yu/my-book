# kafka

---

1. 概念
    - 消息组：一个topic消息可以被多个消费组消费，但组内只能有一个消费者消费。
    - 分区：一个topic可能有多个分区和消费组，每个分区对应一个消费者。分区默认有序性。
    - 消息发送： 每次发送的是一个消息组，是某时间段内的所有消息。
    - broker：消息存放的地方，一般多个机子做集群

2. 为什么快
    1. send_file (现代的unix 操作系统提供了一个高度优化的编码方式):
       原先发送消息流程： 四次复制
       > 磁盘 -> 系统缓存区 -> 用户缓冲区 -> 系统缓冲区的套接字缓冲区 -> 通过网络发送的 NIC 缓冲区
       sendfile(zero-copy（零拷贝）): 磁盘 -> 通过网络发送的 NIC 缓冲区
    2. Memory Mapped Files：
       > Kafka 使用 Memory Mapped Files 完成内存映射，Memory Mapped Files 对文件的操作不是
       write/read，而是直接对内存地址的操作，如果是调用文件的 read 操作，则把数据先读取到内核空间中，然后再复制到用户空间，但
       MMAP可以将文件直接映射到用户态的内存空间，省去了用户空间到内核空间复制的开销

       > Producer生产的数据持久化到broker，采用mmap文件映射，实现顺序的快速写入

       > Customer从broker读取数据，采用sendfile，将磁盘文件读到OS内核缓冲区后，直接转到socket buffer进行网络发送。

3. 消息消费：consumer 的每个请求都在 log 中指定了对应的 offset，并接收从该位置开始的一大块数据。
   > 因此，consumer 对于该位置的控制就显得极为重要，并且可以在需要的时候通过回退到该位置再次消费对应的数据。

4. 设计
    - pull-based 系统：
        - 优点：可以存储到一定的量发送，合理的利用了系统资源
        - 缺点：当没有数据时，consumer会进行长时间pull却没有数据。 有参数可以设置阻塞请求，直到有数据到来。
    - push-based 系统:
        - 优点: 每次有数据都可以及时的发给consumer。
        - 缺点：没有考虑到下游服务的状态。可能搞挂了。
5. 问题
    1. 自动commit，如果一直没有消息，可能一直提交，浪费资源
    2. 手动commit，有同步和异步，如消息一次性处理多的话，可以分批设置offset
    3. 如果发现kafka内存不足，可能是log cleaner线程挂了。

6. 小知识
    1. kafka的单点读写(只读leader)
    2. offset更新：内部通过topic来更新，（原先：频繁操作zk耗资源）
    3. 可配置消息拦截器，消息事务(多个消息一起的事务)，分区重复消息过滤
    4. 使用带有callback的send或commit方法，以便在失败时候做一些处理
    5. props
       1.acks:
        1. all(-1) -> leader收到所有副本Broker的确认消息后，该消息才算是已提交。
        2. (1) 等leader确认才算提交
        3. (0) 不等leader确认就算提交
        4. retries, 配置了retries > 0的Producer能够自动重试消息发送，避免消息丢失。
    7. 消息压缩方式 GZIP，Snappy
7. kafka消费者的分区分配策略
   - 添加topic的命令 `$KAFKA/bin/kafka-topics.sh --create --topic T3 --replication-factor 1 --partitions 1 --zookeeper zookeeper:2181  `
   - 通过配置 ConsumerConfig.PARTITION_ASSIGNMENT_STRATEGY_CONFIG，来切换策略
   - RangeAssignor： 默认的，一个consumer消费所有topic一个partition。
   - RoundRobinAssignor: 多个topic分配给多个consumer消费。 有consumer的增删都会导致全部重新分配
   - StickyAssignor：类似RoundRobinAssignor，但是优化了分配策略，最小移动分区。
   - StreamsPartitionAssignor： kafka-stream 使用的
   - 自定义：通过实现 org.apache.kafka.clients.consumer.internals.ConsumerPartitionAssignor 接口