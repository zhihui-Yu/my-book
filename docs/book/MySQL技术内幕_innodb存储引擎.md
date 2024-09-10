# MySQL技术内幕_innodb存储引擎

---

## INNODB

- innodb中如果表没有主键
    - 表是否有 非空唯一键，有则该字段为主键
    - 没有，则自动创建一个6字节大小的指针
- innodb存储引擎的所有数据都存储在表空间中，表空间由段，区，页(块)组成。
    - 如果启用了 innodb_file_per_table, 则每张表内的数据可以单独放在一个表空间中
    - 即使启用了上面参数，共享表空间也会因为 **系统事务信息**，**二次写缓冲等** 信息而膨胀
- varchar 最大65535，是表内所有字段的最大长度，并不是单个值最大长度，65532才是最大值，2字节表示长度，1字节表示是否为null，不为null，长度为65533，
    - 跟字符集有关系，latin1 -> 65532; gbk -> 32767(65532/2); utf-8 -> 21845(65532/3)
    - 在记录行中保存的是
- char(10) 最小可以存储10个字节的字符，最大可以存储30个字节的字符
- 分区
    - range
        - 每个分区一个区间，对固定函数有优化，其他都是全分区扫描
        - null 的分区： null < 任何非null值
    - list
        - 固定值入固定分区，否则报错
        - 声明 null 放入哪个区，不然会报错
    - hash
        - 自定义hash值，并设置分区数量
        - linear hash：更复杂的hash算法
            - 分布可能不均，但是增删改更快
        - hash(xx(col)=0)
    - key
        - 通过内部hash函数，算出来数据该放哪个分区
        - hash(xx(col)=0)
    - columns
        - 根据字段的值来做分区

## 索引

### B+树

- B是平衡不是二叉，B+树索引并不能找到一个给定键值的具体行，只能找到所在页，在把页读到内存中进行查询。

### 索引的创建

- 旧：先创建一张临时表，然后将数据导入，在删除原表，再把临时表重命名
    - 这样导致大表的索引变更的代价很昂贵，很耗时。
- 新：对表加一个S锁，创建过程中，数据只读。 主键的索引变更还是需要通过临时表进行。
- `show index from table_name;` => `Cardinality`/ `table_rows` 尽可能接近1，该值影响优化器的索引选择
- 对于高选择性的列创建索引才有用处，如果一个查询会查出20%的全表数据，那么可能优化器就会选择全表，即使查询字段游创建索引

### 自适应哈希索引

- 由数据库自己创建，便于字典类型字段的快速查找，需要打开设置 `innodb_adaptive_hash_index=ON`
- 自动创建哈希表的槽数=innodb_buffer_pool_size/256

## Lock

> 观察数据库中的锁和事务

### 三张表查看事务与锁

- INNODB_TRX
    - trx_id innodb存储引擎内部唯一的事务ID
    - trx_state 当前事务的状态
    - trx_started 事务的开始时间
    - trx_requested_lock_id 等待事务的锁ID，trx_state!=LOCK_WAIT,则=null
    - trx_wait_started 事务等待开始的时间
    - trx_weight 事务的权重，反应一个事务修改和锁住的行数。 死锁时，选择值最小的回滚
    - trx_mysql_thread_id mysql中的线程id
    - trx_query 事务运行的sql

- INNODB_LOCKS
    - lock_id 锁id
    - lock_trx_id 事务id
    - lock_mode 锁的模式
    - lock_type 锁的类型
    - lock_table 加锁的表
    - lock_index 锁的索引
    - lock_space innodb存储引擎表空间的id
    - lock_page 被锁住的页的数量，表锁=null
    - lock_rec 被锁住的行的数量，表锁=null
    - lock_data 被锁住的行的主键值，表锁=null (范围查找，只返回第一行的主键值)

- INNODB_LOCK_WAITS
    - requesting_trx_id 申请锁资源的事务id
    - requesting_lock 申请的锁的id
    - blocking_trx_id 阻塞的事务id

### 锁的算法

> mysql 会选择最小范围的锁，next-key lock 是默认的，如果是等值查询则单行锁

- Record Lock 单行锁
- Gap Lock 间隙锁，不含包记录本身
- Next-Key Lock 锁一个范围， 上两种的集合

### 锁升级

- 行锁
- 页锁
- 表锁

> 脏读：读到未提交的数据
> 幻读：同样的sql，多次读到的数据不一致。
> 不可重复读：读到已提交的数据

> RR是mysql默认的隔离级别，避免脏读和不可重复读，但是会有幻读情况。
> 脏页：由于写盘和更新内存页(已经在redo log里面了)是异步的，所以存在不一致，但也提高并发性
> 幻读：如果查询加锁，会避免幻读，因为查询加锁(间隙锁)会阻塞其他事务对范围做修改。

## 备份

### 概述

- 按照备份方法分为： 热备|冷备|温备
- 按照备份后的文件分为： 逻辑(SQL)备份|裸文件(物理文件)备份
- 按照备份数据库内容分为： 完全备份|增量备份|日志备份

### 冷备

- 备份数据库的frm文件，共享表空间文件，独立表空间文件(*.ibd)，重做日志文件。 定期备份my.cnf文件，有利于恢复。
- 优点：
    - 备份简单，拷贝文件。
    - 备份文件易于在不同操作系统，不同MySQL版本上进行恢复
    - 恢复操作简单，拷贝文件到指定位置即可
    - 恢复速度快，不需要执行SQL，也不需要重建索引。
- 缺点：
    - 文件较大
    - 并不总是可以轻易跨平台。操作系统，MySQL版本，文件大小写敏感和浮点数格式都会成为问题。

### 逻辑备份

- 备份语法： mysqldump args > file name
    - mysqldump --all-database > dump.sql
    - mysqldump --database db1 > db1.sql
- 恢复语法： mysql -uroot -p < test_backup.sql
    - 也可以用source命令 source /home/mysql/test_backup.sql
    - 或者使用：load data infile '/home/mysql/a.text' into table x; [可以有更丰富的条件]
    - 或者使用： mysqlimport --use-threads=2 test /home/mysql/t.txt
      /home/mysql/s.txt [类似上一种，但是可以并发导入多个表，实际也是调用`load data infile`]

> 如果dump文件内有删除、创建数据库，要确保当前实例没有相同的存在。
> dump 不包含视图，所以需要手动导出，并在数据回复后，再导入新的环境

### 二进制日志备份与恢复

- 配置中需要启用 log-bin
- 启用其他参数确保安全和正确记录
    - sync_binlog = 1
    - innodb_support_xa = 1
- 在导出前，通过 `flush logs` 命令生成一个新的二进制日志文件，然后备份之前的二进制文件
- 恢复命令
    - mysqlbinlog [options] log_file ...
    - mysqlbinlog binlog.000001 | mysql -uroot -p test
    - mysqlbinlog binlog.[0-10]* | mysql -uroot -p test
- 通过source来恢复，好处是可以修改文件
    - mysqlbinlog binlog.000001 > /tmp/statements.sql
    - mysqlbinlog binlog.000002 >> /tmp/statements.sql
    - mysql -uroot -p -e "source /tmp/statements.sql"
- 指定恢复的偏移量 [--start-position | --stop-position | --start-datetime | --stop-datetime]
    - mysqlbinlog --start-position=107856 binlog.000001 | mysql -uroot -p test

### 热备

- ibbackup: 适用于 MyISAM 和 InnoDB 存储引擎的官方热备工具，在innodb中工作原理如下
    - 记录备份开始时，innodb存储引擎重做日志文件检查点的LSN
    - 拷贝共享表空间文件以及独立表空间文件
    - 记录拷贝完表空间后，innodb存储引擎重做日志文件检查点的LSN
    - 拷贝在备份时产生的重做日志
- ibbackup 优点
    - 在线备份，不阻塞
    - 备份性能好，备份的实质是复制数据库文件和重做日志文件
    - 支持压缩备份，通过选项，可以支持不同级别的压缩
    - 跨平台支持，可以在linux，windows，以及主流unix系统平台上运行。
- 由于ibbackup是收费的，XtraBackup不收费

### 快照备份

- 将数据磁盘快照备份，最好备份到备机上，防止主机磁盘损坏导致数据丢失

### 复制

- 使用MySQL的复制来实现数据的备份，将主机的数据发到备(从)机来实现备份，但是由于主备(从)之间有延迟，所以不能算完全备份。
- 优化： 复制+快照，在从机上做快照，主机如果误操作了，可以把从机的快照拿来恢复数据，从机也要做些权限控制，防止误操作。

## 性能调优

> 数据库分 OLTP(在线事务处理) 和 OLAP(在线分析处理) 两种， 前者多在事务处理应用中，后者在数仓或者数据集市中应用。

- 选择合适的CPU
    - 多核能提升执行效率
- 内存的重要性
    - 数据|索引是有缓存到buffer—pool里面的，所以提高内存或者计算相应缓存池命中率很重要
    - 缓存池命中概率 = [innodb_buffer_pool_read_requests] / [innodb_buffer_pool_read_requests + innodb_buffer_pool_read_ahead + innodb_buffer_pool_reads]
    - 平均每次读取字节数 = [innodb_data_read] / [innodb_data_reads]
    - 硬盘对数据库性能的影响
        - 机械硬盘的寻道时间和转速是重要指标，顺序访问速度远大于随机访问，多块硬盘组成RAID能提高性能，也可以将数据分在不同磁盘达到负载均衡。
        - 固态虽然不需要大量时间定位数据(固态有一致的随机访问时间)，但是数据覆写需要擦除原有数据块。
- 合理设置RAID
- 操作系统的选择也很重要
- 不同文件系统对数据库的影响
- 选择合适的基准测试工
    - `sysbench`  | `mysql-tpcc`

## INNODB 存储引擎源代码的编译与调试
- 网站：https://dev.mysql.com/downloads/mysql/
- 选择长期的版本，选择 linux - Generic，下载。
> 不同版本源码位置可能不同。
