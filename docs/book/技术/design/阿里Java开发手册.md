## 阿里Java开发手册

---
`date: 2022-03-28`

- 使用String来switch时候，注意null的判断，因为switch case里面没有null。

- 三目运算符的表达式1和表达式2的类型会强制一样，可以能会拆箱。
   > 如 flag? 1*Integer : Integer, 由于表达式1拆卸为int了，表达式2 也会拆箱为int，注意NPE。

- 在并发场景，使用大于等于 或着 小于等于，不然可能会并发击穿现象，就是预期是0，但是因为并发变成负数，导致程序没有结束。

- try-catch-finally, finally 中有return 就会直接return，不会用到try里面的。

- DRY原则 -> don't repeat yourself.

- 单元测试原则： AIR(如空气般，畅通无阻) BCDE(Border,Correct,Design,Error)

- count(*)会统计值为 NULL 的行，而 count(列名)不会统计此列为 NULL 值的行。

- NULL 与任何值的直接比较都为 NULL。使用 ISNULL()来判断是否为 NULL 值