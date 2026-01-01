open source project -- mybatis
----
### 前言
推荐几个链接，关于mybatis源码解读讲解的很详细的。

>[手把手带你阅读Mybatis源码（一）构造篇](https://www.cnblogs.com/javazhiyin/p/12340498.html) <br/>
 [手把手带你阅读Mybatis源码（二）执行篇](https://www.cnblogs.com/javazhiyin/p/12344651.html) <br/>
 [手把手带你阅读Mybatis源码（三）缓存篇](https://www.cnblogs.com/javazhiyin/p/12357397.html) <br/>

### 开始之源： 
- SqlSessionFactoryBuilder().builder(...) 返回 SqlSessionFactory;
    > 这一步就是在加载配置(xml,properties), 然后创建相应的mapper对象，configuration... [很多地方用到了反射来实现一种灵活性。]

### 在有 SqlSessionFactory 对象后， 用 openSession() 开启一个 session 与数据库连接。
- 创建session 默认走的是 DefaultSqlSessionFactory 的 openSession(), 创建出一个 DefaultSqlSession : <br/>
    > DefaultSqlSession 内包含的 executor 默认是走 SimpleExecutor, 如果开启 mapper 级别的二级缓存，则会在 SimpleExecutor 上再包一层，就是 CachingExecutor.

### 有了 session , 当然是开始做数据的 DDL 或 DDM 了: 
1. select 调用基本的都是 selectList方法 <br/>
   - 查询时候先看是不是开启二级缓存，开启则先查二级缓存，没有则查一级缓存，也没有就查数据库，将返回的数据存入一二级缓存中。
2. update/delete/insert 调用的都是update <br/>
   - 判断是否需要清理二级缓存，然后判断是否清理一级缓存，然后调用 update 方法。 <br/>
    > 这里调用update是由于在外层已经把sql封装好了，在 SimpleStatementHandler 的时候， 只需要调用 jdbc 并且 传参判断是否需要生成 key 返回就好了。<br/>

> 一级缓存是指 sqlSession 级别的一个map， close sqlSession 了， 该缓存就清理了。 [不可设置的] <br/>
> 二级缓存是指 mapper[namespace] 级别的一个 map， 调用同一个 namespace 的查询，都用同一个cache。[可配置] <br/>
> 开启二级缓存要注意设置过期时间，并且要注意内存溢出 <br/>

---
todo list:
1. xml 配置文件如何解析的
2. mapper调用后发生了什么
3. ErrorContext 设计思想
4. 返回的结果集是怎么封装的