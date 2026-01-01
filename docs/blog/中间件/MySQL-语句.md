# MySQL 语句

---

注意：
> 在事务中，UPDATE DELETE 也会索数据行，如果A UPDATE 没有提交，那B DELETE 会一直阻塞。

## 交换两个字段的值：
1. `UPDATE orders as a, orders as b SET a.xx = b.xx, a.xx = b.xx WHERE a.xx < a.xx;` [100w 条 修复0.4k数据 耗时极慢]
2. `update test_swap set x=(@t:=x), x=y, y=@t;` (性能更佳，主键全表查一次就好)


## 修改字段属性：
`ALTER TABLE table_name [MODIFY (COLUMN) | CHANGE] COLUMN_NAME VARCHAR(20) NOT NULL;` (读x次，写x次，相当于重建)

- 更快的写法
`ALTER TABLE table_name ALERT COLUMN COLUMN_NAME SET DEFAULT xxx;` 直接修改.frm文件，不查询表数据
> 注意： 修改字段属性时，如果是null->not null, 要先将字段填充属性，然后再更新表字段属性。

## 修改字段名称

`ALTER TABLE table_name CHANGE (COLUMN) COL_NAME COL_NAME_2 VARCHAR(50) (NOT NULL);`  默认不写就是null

## 修改表名
`ALTER TABLE user RENAME users`

## 添加字段
`ALTER TABLE users ADD (COLUMN) age INT(3) NOT NULL [AFTER / BEFORE COL_NAME]`

## 创建索引：
`CREATE INDEX indexName ON table_name (column_name)`

## 删除索引：
`ALTER TABLE table_name DROP INDEX index_name;`

## 子查询判断有无匹配数据：
`SELECT * FROM orders where exists (SELECT 1 FROM order_item oi where oi.order_id = orders.id and item_name = "");`
(SELECT 1 是因为，如果查询结果没有值的话，就什么都没有，如果有值就都显示1. ps: 默认表明可做别名。)

## 窗口函数 -- LAG/LEAD
```sql
LAG(<expression>[,offset[, default_value]]) OVER (
    PARTITION BY expr,...
    ORDER BY expr [ASC|DESC],...
)
```
解释：
- LAG()函数可用于计算当前行与上一行之间的差异。
    - 对结果集按照partition 分区后，[order by 排序] 然后找当前行的上[offset]行。
- LEAD() 函数 与LAG() 效果相反


```sql
CREATE TABLE tax_revenue (
  id INT AUTO_INCREMENT PRIMARY KEY,
  year CHAR(4) NOT NULL,
  quarter CHAR(1) NOT NULL,
  revenue INT NOT NULL
);

INSERT INTO tax_revenue
  (year, quarter, revenue)
VALUES
  ('2020', '1', 3515),
  ('2020', '2', 3678),
  ('2020', '3', 4203),
  ('2020', '4', 3924),
  ('2021', '1', 3102),
  ('2021', '2', 3293),
  ('2021', '3', 3602),
  ('2021', '4', 2901);

-- 在每行的后面添加下一个季度的营收
SELECT
  *,
  LAG(revenue, 1, 0) OVER ( -- 取营收字段，当前行的下一行
    PARTITION BY year -- 按年分区
    ORDER BY quarter DESC -- 按季度排序
  ) next_quarter_revenue
FROM tax_revenue;
```

