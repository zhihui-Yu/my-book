Netty

---

1. BIO,NIO,AIO区别
    1. BIO 阻塞IO，多条连接对应一个线程，每个连接都需要等前面连接处理结束后才能被处理
    2. NIO 非阻塞IO， 后面的连接不需要等前面的连接处理结束，就可以被处理。 此处有许多种实现
    3. AIO 异步非阻塞IO，在NIO基础上进行优化，NIO的IO操作还是同步的，所以AIO是异步调用buffer的write或者read，然后buffer处理完后回调主流程
2. Java socket编程
    1. Buffer : 缓存，有多种类型ByteBuffer,IntBuffer... 线程安全
    2. InetSocketAddress: 配置socket的端口号
    3. Selector: 多路选择器，用于监听channel的， windows和linux的实现不一样. selector.select()可以知道是否发生事件
    4. SelectionKey: 监听事件，READ，ACCEPT，WRITE,CLOSED...
    5. Channel: 通道，一个通道对应一个IO的Buffer，通道着重强调对Buffer的读写
    6. ServerSocketChannel: 服务器的socket channel，可以理解为一个主的channel，监听连接并accept后，<br/>
       得到一个新的SocketChannel，将新的channel注册到Selector中就可以监听新的channel发生的事件。<br/>
       （用channel的register方法将channel注册到selector，并可以设置感兴趣的监听事件）
3. 零拷贝
    1. 原生的拷贝场景 <br/>
       用户态 -> 系统态 -> 用户态 -> 系统态<br/>
       文件直接拷贝到内核内存(DMA) -> （CPU）拷贝到用户内存 -> （CPU）拷贝到系统态的Socket Buffer -> 传输<br/>

    2. mmap：内存映射, 将内核内存映射到用户内存，使得用户内存与内核内存使用的是同一个数据源，减少一次拷贝 <br/>
       用户态 -> 系统态 -> 用户态 -> 系统态<br/>
       文件直接拷贝到内核内存(DMA)，并共享到用户内存 -> （CPU）拷贝到系统态的Socket Buffer -> 传输<br/>
    3. sendFile: 一次CPU拷贝，由DMA拷贝到kernel后直接可以被拷贝到socket buffer
       用户态 -> 系统态 -> 系统态<br/>
       文件直接拷贝到内核内存(DMA) ->（CPU）拷贝到系统态的Socket Buffer -> 传输<br/>
       > java 用 channel 的 transferTo 方法， windows有限制一次最大传输多少M，linux没有
4. 为什么用netty
    1. 使用java原生的api实现，难度大，容易有bug
    2. netty封装了java原生的api，使用上更加便捷，社区活跃
5. reactor模型架构
    1. 单reactor单线程 accept和read/write都在一个线程（像BIO）
    2. 单reactor多线程 accept后独立线程组去监听read/write事件并处理 （NIO）
    3. 多reactor多线程 （Netty使用的）
       多个线程各自监听各自的selector，在accept将channel的read/write监听工作交给worker线程组(主要做IO buffer操作)，<br/>
       然后worker可以将获取的数据交由单独线程处理具体的业务逻辑，但是要返回结果给worker,worker会将结果返回channel
6. netty
    1. bootstrap, ServerBootStrap：客户端或者服务器的一个启动对象，服务器一般需要bossGroup+workGroup来实现多reactor多线程
        1. handler()：定义bossGroup的channel的handler，
        2. childHandler()：定义workGroup的channel的handler
    2. EventLoop：维护一个自己的Selector对象，监听事件并做相应的处理
    3. EventLoopGroup,NIOEventLoopGroup: 一组EventLoop的抽象，用next()获取一个EventLoop来处理相应的channel发生的事件
    4. Pipeline：处理数据的管道，有先后顺序，可以自定义。
        1. IdleStateHandler: 手动添加到管道中用心跳检测，检测连接的读写状态
    5. ChannelHandlerContext：包含channel的上下文数据，如Pipeline，ChannelHandler的信息。
    6. Unpooled： netty 提供的一种buffer 操作工具，内部定义了readIndex，writeIndex，capacity，以方便读写
    7. ChannelOption: channel 相关的设置，如SO_BACKLOG(连接队列大小)，SO_KEEPALIVE
    8. SimpleChannelInboundHandler/SimpleChannelOutboundHandler
    9. HttpObjectAggregator：http数据较大时，会变成多次分段请求，这个会将分段请求合并
    10. WebSocketServerProtocolHandler(path): 声明具有 ws 协议的请求路径
    11. XXXEncoder/XXXDecoder 用于加解码传输的数据，每种解码器都有自己的规则，以防粘包或以便拆包
7. protobuf
    1. 由于jdk的序列化性能不高，所以使用protobuf这种轻量级的数据存储格式
    2. 常见的的http+json逐渐转成tcp+protobuf
    3. 跨语言，支持不同语言的服务器之间传输，解码
8. 粘包拆包 ？ 为什么变成对象就知道长度呢，如果对象太大了，会变成发送多次吗？那还会有粘包拆包问题吗
    1. netty 默认的读取时没有限制读取的字节长度，导致有多少数据就读了多少，可能会多个包被同时读取，也可一份数据要读多次才完整
    2. 使用自定义的协议 + 自定义加解码器解决 （netty会根据数据类型走不同的加解码器，加解码器内定义了每次读取的数据大小，多少算完整）