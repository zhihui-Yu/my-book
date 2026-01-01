# flyway

---

- 一种数据库版本控制工具 [document](https://flywaydb.org/documentation/getstarted/why)

### 两种文件 V 和 R
V: V 开头是不可重复执行的文件，每次修改完都该更改名称
R: R 开头是可重复执行的文件，需要保证内部sql都是可以重复执行的

名称格式： V__table_name.sql, R__table_name.sql

### 操作
`baseline`: 以现在数据库状态为基准，创建 `flyway_schema_history`表，以及相关信息填充 [类似初始化]

`migrate`: flyway根据sql的变化来进行更新

`repair`: 对最近的迁移失败做一次修复 [类似回滚]

`undo`: 撤销最近一次的版本升级，无论成功与否

`clean`: 删除表，包括 `flyway_schema_history`

`info`: 打印所有迁移的信息，包括版本变化

`validate`: 校验本次迁移


### 原理
在第一次执行flyway时候，会创建一个名为 `flyway_schema_history` 的表，其存放的是每次迁移的结果。
flyway在后续迁移动作时，会校验文件名称以及是否修改，然后做相应的动作。


### 坑
1. 对于R文件，如果在`flyway_schema_history`中有记录，则不能直接删除，需要保留文件[或者直接删除`flyway_schema_history`表中对该文件的所有记录 '不好']。
2. 对于执行失败后，需要执行repair后，才能进行下一次操作，[或者将`flyway_schema_history`中记录`success`改为true [不好]]


