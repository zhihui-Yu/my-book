# 副本集与分片

---

## 副本集(replica set)
- 概念:mongo的主从模式一样。mongo可以设置自己的副本集来达到高可用，副本集有主从之分，从就是备份主的数据。
    部署机器设置奇数最佳，这样选举只要某个机器有一半以上的投票就可以是主节点。 主节点挂了，从节点之间会在选举一个。
- 组成： 主、 从、 仲裁节点(Arbiter)
- 命令：
  - rs.help(): 查看帮助
  - rs.initiate();: 初始化(一般启动后先执行这个)
  - rs.status(): 查看节点状态
  - rs.add("host:port"):  添加到副本集

## 分片
- 概念
<pre>
    mongo可以将数据切分多片(区)，每个片存一部分数据，这样就可以达到易水平扩展的好处。
    但是选择一个合理的片键很关键，不然分布不均可能导致查询到分片内数据量大时候速度比较慢。
    可以为分片创建副本集。
</pre>

- 搭建需要： mongos,configserver,shardding分片
  - Mongos:路由服务是Sharded cluster的访问入口,本身不存储数据
  - Configserver: 配置服务器，存储所有数据库元信息（路由、分片）的配置。
  - 分片（sharding）是指将数据库拆分，将其分散在不同的机器上的过程。
- 命令
  - sh.addShard("[副本集名称/]host:port[,...]") 添加分片
  - sh.status()  查看状态
  - db.runCommand( { enablesharding :"testdb"}); 使testdb可以进行分片
  - db.runCommand( { shardcollection : "testdb.table1",key : {id: "hashed"} } ): 设置分片的集合和片键
  - db.table1.stats(); 查看db状态
  - db.runCommand({listshards: 1}): 查看分片集群的信息：

- 节点有问题，需要重新配置时：
- rs.reconfig({_id: "dev",version: 1,members: [{ _id: 0, host : "localhost:27017" }]},{force:true})