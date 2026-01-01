消息中间件之RabbitMQ
---

## 分布式系统中消息中间件的作用

- 流量控制： 并发请求，以消息队列模式消费
- 异步处理： 将非主要的任务以消息的形式异步处理
- 应用解耦： 用消息来处理不同系统间交互

## 消息协议

- JMS -> java message service, 原生的java消息规范
- AMQP -> 网络级协议，支持多种消息模型。

## RabbitMQ

> 由erlang开发的AMQP开源消息中间件

#### 概念

- message: 有消息头和消息体构成的消息，
- publisher: 消息生产者
- broker：用来管理消息的服务器
- consumer：消息的消费者
- exchange：用来接收生产者发送的消息，并将消息路由给服务器内的队列
- queue：存储消息的队列

#### 消息流转

publisher -> broker[exchange -> queue] -> consumer

- publisher 到 broker 时，通过 route-key 来确定消息具体到哪个 queue
- exchange 会 binding 多个 queue，所以需要 route-key 确定。
- publisher 到 broker 是通过一个长连接监听，连接内部为多 channel 实现 (多路复用)
- consumer 监听broker也是通过一条长连接，内部多路复用

#### exchange 类型

- direct： 点对点传输模式，route-key和binding-key精确匹配，就只会发送到对应的地方。

- fanout： 发布订阅模式，忽略route-key，没收到一条消息，exchange就会把消息存储到当前exchange内所有queue。

- topic： 类似发布订阅模式，binding-key为通配模式，只要route-key符合binding-key模式，就会被发到相应的queue中。
  > '#' -> 0或多个单词， '*' -> 一个单词

- headers： 不用route-key，而是使用headers里面的arguments，只要headers内包含的参数与exchange在bind-queue时候设置的arguments一样，就会发送到相应的queue。
  > x-match: 多个argument参数时的路由规则, any就是OR，all 就是 AND。

#### Springboot 集成 rabbitMQ

- 引入依赖 springboot-ampq-rabbitmq
- 使用注解@EnableRibbit标记启用rabbit
- 使用AmqpAdmin 来创建queue，exchange，binding。
- 使用RabbitTemplate来发送消息
- 使用注解@RabbitListener或者@RabbitHanler来接收消息
- 默认使用SimpleMessageConvert，我们可以给容器注入Jackson2JSONMessageConvert来实现转换成json传输。

#### 消息可靠投递

- publisher -> broker[exchange -> queue] -> consumer : 每一个箭头都有可能失败
  > 如果在channel上设置事务，性能会降低250倍
- 使用回调机制实现
  - confirmCallback: publisher 到 broker 了，发生的回调
    > spring.rabbitmq.publisher-confirms=true
  - returnCallback : 消息从 exchange 到 queue失败了，发生的回调
    > spring.rabbitmq.publisher-returns=true<br/>
    > spring.rabbitmq.template.mandatory=true # 只要抵达queue，优先以异步方式发送回调
  - 消费者使用手动ack模式,防止消费失败或者没消费场景下消息自动删除了
    > spring.rabbitmq.listener.simple.acknowledge-mode=manual <br/>
    > 使用channel.basicAck(message.getMessageProperties().getDeliveryTag(), false);// 非批量签收<br/>
    > 使用channel.basicNAck(message.getMessageProperties().getDeliveryTag(), false,false);// 非批量拒收，最后的false表示退货，不会把消息重新放入队列<br/>
    > channel是消费者的消费方法的入参，会由spring自动注入，表示当前连接通道
  