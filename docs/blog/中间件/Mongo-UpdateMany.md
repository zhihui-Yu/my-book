# MongoDB 之 UpdateMany

---

## 使用 UpdateMany

> https://www.mongodb.com/docs/v6.0/reference/operator/update/#update-operators

```mongodb
db.collection.updateMany(
    <filter>,
    <update>,
    {
        upsert: <boolean>,
        writeConcern: <document>,
        collation: <document>,
        arrayFilters: [ <filterdocument1>, ... ],
        hint:  <document|string>        // Available starting in MongoDB 4.2.1
    }
)
```

### 常规用法之 [Update document](https://www.mongodb.com/docs/v6.0/reference/operator/update/#std-label-update-operators)

#### 使用
  ![image](https://raw.githubusercontent.com/zhihui-Yu/images/main/mongodb/update/update-operators.png)

- 在这里的 `$set` 只能把字段的value变成固定值，既 `{field: value}`，没办法做过多转换

```text
db.order.updateMany({"_id":"xxx"},{$set:{comment:"new comment"}});
```

#### updateMany 支持的 update operators

  ![image](https://raw.githubusercontent.com/zhihui-Yu/images/main/mongodb/update/fields.png)
  ![image](https://raw.githubusercontent.com/zhihui-Yu/images/main/mongodb/update/array.png)
  ![image](https://raw.githubusercontent.com/zhihui-Yu/images/main/mongodb/update/modifier&bitwise.png)

> 这些支持了我们大部分的使用场景，但是如果我想更新一个字段的类型呢？

#### 更新字段类型语句

> 先说结果，感兴趣可以继续看下去

```text
db.order_configs.updateMany(
  { "_id": "xxx" }, 
  [
    { $set: { "price": { $toDouble: "$price" } } }
  ]
);
```

### 另有玄机之 [Aggregation pipeline](https://www.mongodb.com/docs/v6.0/reference/method/db.collection.updateMany/#update-with-an-aggregation-pipeline)

  ![image](https://raw.githubusercontent.com/zhihui-Yu/images/main/mongodb/update/update_with_aggregation_pipeline.png)

#### Aggregation pipeline 中的 `$set`
  ![image](https://raw.githubusercontent.com/zhihui-Yu/images/main/mongodb/update/agg-pipe-set.png)

> https://www.mongodb.com/docs/v6.0/reference/operator/aggregation/set/#definition

- 可以看出来，这里的 `$set` 使用的是 `{ $set: { <newField>: <expression>, ... } }`, 而不再是一个简单的value.
- 我们再来看看 `<expression>`是什么?

  ![image](https://raw.githubusercontent.com/zhihui-Yu/images/main/mongodb/update/agg-pipe-expressions.png)


> 这里有很多可操作的类型，就不枚举了。感兴趣看文档 https://www.mongodb.com/docs/v6.0/meta/aggregation-quick-reference/#std-label-aggregation-expressions

#### 更新字段的类型

```text
db.order_configs.updateMany(
  { "_id": "xxx" }, 
  [
    { $set: { "price": { $toDouble: "$price" } } }
  ]
);
```

- `{ $toDouble: "$price" }` 是一个 expression，`"$price"` 也是一个 expression. 前者是一个operator，后者是一个text，`$`指当前文档

  ![image](https://raw.githubusercontent.com/zhihui-Yu/images/main/mongodb/update/agg-pipe-toDouble.png)



> mongo的操作各式各样，感兴趣大家可以自行查看文档来寻找自己需要的功能