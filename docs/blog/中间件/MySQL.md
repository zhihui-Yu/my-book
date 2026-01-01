# MySQL

---

## 字符集排序规则
- 以 _ci 结尾是不区分大小写
- 以 _cs 结尾是区分大小写
- 以 _bin 结尾是以字符二进制值比较

## 系统变量
```sql
show global variables like 'innodb_buffer_pool_size';

show global status like 'Innodb_buffer_pool_pages_data';
show global status like 'Innodb_buffer_pool_pages_total';
show global status like 'Innodb_page_size';
show variables like 'max_connections';
show variables like 'max_use_connections';

show global variables like '%innodb_buffer%';

SHOW ENGINE INNODB STATUS;

show status like 'Threads%';

show global status like 'Thread%';

show processlist;

-- 查看版本。
select version() from dual;
```

## procedure 基础案例
```sql
CREATE PROCEDURE in_param ( IN p_in INT )
BEGIN
	SELECT p_in;
	SET p_in = 2;
	SELECT p_in;
END

call in_param(5)
```

## mysql 锁相关知识

- 数据库级别
    - 全局锁：锁整个数据库，不可写，只读
        - 数据备份时，如果不加该锁，则可能导致数据不一致。
        - 加锁：`flush tables with read lock;`
        - 解锁 `unlock tables;`
- 表级别
    - 表锁：
        - 表共享读锁（read lock）：其他客户端不可写，只读
        - 表独占写锁（write lock）：其他客户端不可读写
        - 加锁：lock tables 表名... read/write。
        - 释放锁：unlock tables / 客户端断开连接 。
    - 元数据锁：元数据-> 表结构数据
        - 为防止在数据更新时，对元数据更新，系统自己加的锁。
        >   查看锁情况 `select object_type,object_schema,object_name,lock_type,lock_duration from performance_schema.metadata_locks;`

    - 意向锁： 如果表有行锁，会自动加意向锁，为了减少表锁时候对每行检测是否具有行锁
        - 意向共享锁(IS): 由`select ... lock in share mode`添加。与表锁共享锁(read)兼容，与表锁排他锁(write)互斥。
        - 意向排他锁(IX): 由`insert、update、delete、select...for update`添加。与表锁共享锁(read)及排他锁(write)都互斥，意向锁之间不会互斥。
        >   查看锁情况： `select object_schema,object_name,index_name,lock_type,lock_mode,lock_data from performance_schema.data_locks;`
- 行级别
    - 行锁： 锁定单个行记录的锁，防止其他事务对此行进行update和delete。在RC、RR隔离级别下都支持。
        - 共享锁（S）：允许一个事务去读一行，阻止其他事务获得相同数据集的排它锁。[SELECT ... LOCK IN SHARE MODE 加S]
        - 排他锁（X）：允许获取排他锁的事务更新数据，阻止其他事务获得相同数据集的共享锁和排他锁。 [INSERT,DELETE,UPDATE,SELECT ... FOR UPDATE都会加X]
        - InnoDB的行锁是针对于索引加的锁，不通过索引条件检索数据，那么InnoDB将对表中的所有记录加锁，此时就会升级为表锁。
        > 查看锁情况： `select object_schema,object_name,index_name,lock_type,lock_mode,lock_data from performance_schema.data_locks;`
    - 间隙锁： 锁定索引记录间隙（不含该记录），确保索引记录间隙不变，防止其他事务在这个间隙进行insert，产生幻读。在RR隔离级别下都支持。可多个事务共存间隙锁。
    - 临键锁： 行锁和间隙锁组合，同时锁住数据，并锁住数据前面的间隙Gap。在RR隔离级别下支持。
        - 向右遍历时最后一个值不满足查询需求时，next-key lock 退化为间隙锁。[锁最后一个值到无穷的间隙，防止事务过程中有数据插入]
         > InnoDB的B+树索引，叶子节点是有序的双向链表,所以最右侧没有数据说明，找不到符合条件的数据，所以要锁空白记录

> refer to https://juejin.cn/post/7208019379828621373

## 8.0+之 with语句

### 使用方法：
```sql
  WITH
    cte1 AS (SELECT a, b FROM table1),
    cte2 AS (SELECT c, d FROM table2)
  SELECT b, d FROM cte1 JOIN cte2
  WHERE cte1.a = cte2.c;
```

### 递归公用表表达式
- 递归公用表表达式是具有引用其自身名称的子查询的表达式.例如：
```sql
WITH RECURSIVE cte (n [, col_name]) AS
(
  SELECT 1
  UNION ALL
  SELECT n + 1 FROM cte WHERE n < 5
)
SELECT * FROM cte;
```

### 限制公用表表达式递归 [8.0.19]:
- 您还可以执行此操作。因此，以下 CTE 在返回一万行或运行一千秒后终止，以先发生者为准：
```sql
WITH RECURSIVE cte (n) AS
(
  SELECT 1
  UNION ALL
  SELECT n + 1 FROM cte LIMIT 10000
)
SELECT /*+ MAX_EXECUTION_TIME(1000) */ * FROM cte;
```
> 可以使用递归实现多种多样的功能. more details see https://dev.mysql.com/doc/refman/8.0/en/with.html


## 外键

### mysql 外键配置

> doc https://dev.mysql.com/doc/refman/8.0/en/create-table-foreign-keys.html
> 
```mysql
[CONSTRAINT [symbol]] FOREIGN KEY
    [index_name] (col_name, ...)
    REFERENCES tbl_name (col_name,...)
    [ON DELETE reference_option]
    [ON UPDATE reference_option]

reference_option:
    RESTRICT | CASCADE | SET NULL | NO ACTION | SET DEFAULT 

example: 
  在编写创建关联表语句时添加
  FOREIGN KEY (field_name) REFERENCES main_table_name(main_t_field_name) ON DELETE CASCADE ON UPDATE CASCADE
  
  drop:
  ALTER TABLE main_tb_name DROP FOREIGN KEY idx_name;
```

- 作用
    - 可以保证数据的强一致性
    - 使用 CASCADE 可以保证级联更新和删除
- 坏处
    - 一刀切的更新，强一致，有时可能只想删除一部分数据
    - 如果级联数据很大，那可能把mysql弄雪崩

- 文章
    - cascade 实践： https://www.cnblogs.com/zxf100/p/6812269.html
    - 使用外键和不用外键的考量： https://draveness.me/whys-the-design-database-foreign-key/


## SQL 优化
> 每一个语句都应该自己测试过，修改过，然后再测试过，才能知道实际的性能那个好。

### 分页查询：
可以用如下方式： `Select t from t inner join (Select id from t where xx = ? order by xxx asc limit xx,xx) AS t1 on t.id = t1.id`
- 用IN() 在子查询中的：
- 思考是否可以用 EXISTS(子查询) 或者 NOT EXISTS(子查询)

### 索引顺序
- 每一个查询mysql都会创建一个handler 去调用存储引擎的API 同查询索引数据或则下一条数据等。
- 要固定多表连接顺序可以用STRAIGHT_JOIN，不然Mysql可能会进行顺序的优化。

### mysql 突然崩坏，可以用check table 来看表是不是坏了。
使用 REPAIR TABLE 来修复，如果不支持 可以用 `ALERT TABLE xx ENGINE=INNODB` 命令。

`ANALYZE TABLE` 来重新生成统计信息

`SHOW INDEX FROM xxx` 查看索引信息

### 数据碎片优化
> 跟修复表很像
优化：如果正常的索引无法满足现在的要求，可以尝试反范式的sql来优化。 如 IN (xx，xx),IN 内值少的时候可以用

考虑是否需要拆分多个来执行

1. 唯一键最好不为空， 如果可空，则可以重复插入null
2. 联合索引中如果有可空的键，则会导致联合索引(UNIQUE KEY)失效
3. 索引是在用时，load到内存，如果内存不足，将导致load到磁盘，然后导致查询效率急剧降低。


## 小坑
1. 如果inner join 不加 on 条件，那相当于 t1 * t2 表的数量， 每一条 t1 数据都要和 t2 所有数据结合。
2. transaction 如果在中间sql执行错误了，不会执行到commit，所以看起来像是回滚了。
    1. 但是如果在报错后还执行commit，那就会把没错的sql 提交。
    2. 如果在事务中内嵌事务，那内嵌前的sql会被提交。
3. 修改字段属性时，如果是null->not null, 要先将字段填充属性，然后再更新表字段属性。