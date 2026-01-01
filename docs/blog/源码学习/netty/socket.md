## Netty Socket

---

> version: 4.1.72.Final

> netty优点：高度可自定义化的网络编程 <br/>
> 本质为一个可配置的多reactor多线程模型，由一个accept线程在接收socket channel后交由worker线程去监听新连接事件，再由worker去做数据交互等工作。

### 测试代码
```java
public static void main(String[] args) throws Exception {
    //创建两个线程组 boosGroup、workerGroup
    EventLoopGroup bossGroup = new NioEventLoopGroup(); // 默认为Math.max(1, SystemPropertyUtil.getInt("io.netty.eventLoopThreads", NettyRuntime.availableProcessors() * 2));
    EventLoopGroup workerGroup = new NioEventLoopGroup();
    try {
        //创建服务端的启动对象，设置参数
        ServerBootstrap bootstrap = new ServerBootstrap();
        //设置两个线程组boosGroup和workerGroup
        bootstrap.group(bossGroup, workerGroup)
            //设置服务端通道实现类型，netty实现的，非jdk
            .channel(NioServerSocketChannel.class)
            //设置线程队列得到连接个数
            .option(ChannelOption.SO_BACKLOG, 128)
            //设置保持活动连接状态
            .childOption(ChannelOption.SO_KEEPALIVE, true)
            //使用匿名内部类的形式初始化通道对象
            .childHandler(new ChannelInitializer<SocketChannel>() {
                @Override
                protected void initChannel(SocketChannel socketChannel) throws Exception {
                    //给pipeline管道设置处理器
                    socketChannel.pipeline().addLast(new MyServerHandler());
                }
            });//给workerGroup的EventLoop对应的管道设置处理器
        System.out.println("java技术爱好者的服务端已经准备就绪...");
        //绑定端口号，启动服务端
        ChannelFuture channelFuture = bootstrap.bind(6666).sync();
        //对关闭通道进行监听
        channelFuture.channel().closeFuture().sync();
    } finally {
        bossGroup.shutdownGracefully();
        workerGroup.shutdownGracefully();
    }
}
```

### bossgroup 配置数量是否有用
bossgroup是accept线程池，由于服务只监听一个端口，所以有也只有一个线程。

### 何时创建 ServerSocketChannel 并监听 Accept 事件
```java
// bind时候做了channel的初始化 io.netty.bootstrap.AbstractBootstrap#doBind
bootstrap.bind(prot)

private ChannelFuture doBind(final SocketAddress localAddress) {
    final ChannelFuture regFuture = initAndRegister(); // 做连接的初始化
    final Channel channel = regFuture.channel();

    // 异常则直接返回
    if (regFuture.cause() != null) {
        return regFuture;
    }

    // 关闭事件监听
    if (regFuture.isDone()) {
        ChannelPromise promise = channel.newPromise();
        doBind0(regFuture, channel, localAddress, promise);
        return promise;
    } else {
        final PendingRegistrationPromise promise = new PendingRegistrationPromise(channel);
        regFuture.addListener(...);
        return promise;
    }
}


final ChannelFuture initAndRegister() {
    Channel channel = null;
    try {
         // ReflectiveChannelFactory.newChannel() => NioServerSocketChannel, 既测试代码中配置的那样， 
         // 这里初始化channel对象时，调用了 provider.openServerSocketChannel(); 和 channel.configureBlocking(false);
        channel = channelFactory.newChannel();
        init(channel); // 执行 io.netty.bootstrap.ServerBootstrap#init，对channel进行配置, 如pipeline, handler, options
    } catch (Throwable t) {
        ...
    }

    ChannelFuture regFuture = config().group().register(channel); // 绑定到bossgroup的一个线程中，监听channel的accept事件， 这也就是为什么bossgroup配多个线程也只有一个有用的原因
   
    if (regFuture.cause() != null) {  // 异常处理
        ...
    }
    return regFuture;
}
```
### 在发现一个新的连接时，是如何处理的
accept -> run workder -> handler -> pipeline

### EventLoop 有什么用， NioEventLoop 又有什么作用
NioEventLoopGroup 是包含了一组的 NioEventLoop 的对象
NioventLoop 实现了 EventLoop，EventLoop 是个接口，定义了一个方法获取当前 NioEventLoop 所属的 EventLoopGroup。

```java
io.netty.channel.nio.NioEventLoop#run
// 一直轮询自己的NIOEventLoop, 查看是否有新的事件发送，并执行taskQueue中的任务
```