# MongoDB-migration

---

## 更新字段

- 删除某个字段(`$unset:{"field name":"whatever, no impact"}`)

```shell
db.getCollection("test").updateMany({}, {$unset: {"field_1.$[].field_1_1": 1,"field_2": 1}})
```

## 初始化字段

### 给某个字段的初始化为0/ 添加该字段
```shell
db.test.updateMany({"_id": {$ne: null},"field_1":{$ne:null}, "field_1":{$ne:[]}}, { $inc: { "field_1.$[].field_1_1": 0 } });
```

### 初始化数组内的某个字段
```shell
db.test.find({"_id": {$ne: null},"field_1":{$ne:null}, "field_1":{$ne:[]}}).forEach(function(doc){
    var field_1_var = [];
	doc.field_1.forEach(function(d) {
		var total_d = d.amount;
		d.total_d = total_d;
		field_1_var.push(d);
	})
	db.order_modify_records_v3.update({ _id: doc._id }, { $set: { "field_1": field_1_var } })
})
```

## 更改字段类型 
> https://www.mongodb.com/docs/v6.0/reference/method/db.collection.updateMany/#update-with-aggregation-pipeline
```shell
db.test.updateMany(
    { "_id": { $ne: null }, "field_1": { $ne: null } },
    [{ $set: { "field_1.field_1_1": { $toDouble: "$field_1.field_1_1" } } }]
);
```