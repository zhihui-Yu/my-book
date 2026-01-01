# MongoDB-索引

---

## 3.2+ 默认存储引擎：wiredTiger
MongoDB支持多种类型的索引，包括单字段索引、复合索引、多key索引、文本索引等，每种类型的索引有不同的使用场合。

### 单字段索引 （Single Field Index）
`db.person.createIndex( {age: 1} )`
{age: 1} 代表升序索引，也可以通过{age: -1}来指定降序索引，对于单字段索引，升序/降序效果是一样的。

复合索引 (Compound Index)
     db.person.createIndex( {age: 1, name: 1} )
     遵守最左前缀原则，如果age 相同，就按name排序。

### 多key索引 （Multikey Index）
当索引的字段为数组时，创建出的索引称为多key索引，多key索引会为数组的每个元素建立一条索引。

### 其他类型索引
- 哈希索引（Hashed Index）是指按照某个字段的hash值来建立索引，目前主要用于MongoDB Sharded Cluster的Hash分片，hash索引只能满足字段完全匹配的查询，不能满足范围查询等。
- 地理位置索引（Geospatial Index）能很好的解决O2O的应用场景，比如『查找附近的美食』、『查找某个区域内的车站』等。
- 文本索引（Text Index）能解决快速文本查找的需求，比如有一个博客文章集合，需要根据博客的内容来快速查找，则可以针对博客内容建立文本索引。
 - 索引额外属性: MongoDB除了支持多种不同类型的索引，还能对索引定制一些特殊的属性。

唯一索引 (unique index)：保证索引对应的字段不会出现相同的值，比如_id索引就是唯一索引

TTL索引：可以针对某个时间字段，指定文档的过期时间（经过指定时间后过期 或 在某个时间点过期）

部分索引 (partial index): 只针对符合某个特定条件的文档建立索引，3.2版本才支持该特性

稀疏索引(sparse index): 只针对存在索引字段的文档建立索引，可看做是部分索引的一种特殊情况

> 用 db.xxx.find({xxx: 18}).explain() 来查看执行计划, 主要看winningPlan$stage的值：IXSCAN(索引)，COLLSCAN (全表)