# CRDT
> conflict-free replicated data type（无冲突复制数据类型）它是一种数据类型，或者说是方案，确保在网络中的不同副本最后数据保持一致的，常用于协同编辑领域。

---

## 介绍
CRDT 在 2011 年在论文中被正式提出，虽相比 OT 算法（1989年）起步晚了很长的时间，但实现难度低很多，且出现了高性能的 CRDT 库 Y.js，越来越多产品选择使用 CRDT 来实现协同编辑功能。
其也衍生了很多分支模型，如 `AWSet`,`RWSet`,`LWW`,`2P-Set`,`G-Counter`,`PN-Counter`.

> OT(Operational Transformation),操作是有序的，后续操作可能依赖于前面的操作。并发时，使用转换函数来保证顺序从而实现一致性。

## CRDT 的类型
> CRDT 主要分为两大类型：Operation-based 和 State-based。

### Operation-based (传输的数据量较少)
- 副本进行同步时，只会把新增的本地操作（operation）发送出去。 另一个副本拿到这个 operation 会将其应用到自己的状态上，operation 需要满足交换律（commutative）。
  > 交换律，指的是交换运算顺序，最后的结果不变。比如加法就满足交换律，a+b 和 b+a 的结果是相等的。 operation 之所以要满足交换律，是因为网络并不可知, 保证在不同顺序下，结果是一致的。
- 在js框架中，通常我们是通过 Generator 函数生成新的 operation，发送给其他副本，然后这些副本通过  Effector 函数应用这些副本。

> 因为交换律这个特性，Operation-based CRDTs 还有另一个名字 commutative replicated data types（CmRDTs）。

### State-based (实现更简单, 但文档大时，全量传输耗时长)
- 一个副本进行同步时，会将整个完整的本地状态（state） 发送出去。另一个副本需要支持将其他副本进行合并（merge）的操作，这个 merge 方法需要满足交换律、分配律，以及幂等性。
> 如果数据量不大，是可以考虑使用的。 State-based CRDTs 同样也有另一个名字：Convergent Replicated Data Types（CvRDTs）。Convergent 是收敛的意思。

## 模型
### AWSet [Add-wins set，一种新增优先于删除的集合数据结构]
- 如果两个副本同时变更，且一个删除A，一个新增A，则A保留。
> 为判断两个操作是否是 “同时” 的，我们会附加一个和时序相关的元数据，比如时间戳、版本向量。

### RWSet [Remove-win set，一种删除优先新增的集合数据结构]
- AWSet 类似，但对于并发的操作，会保留删除，丢弃新增。

### LWW [Last-writer-wins，最后写入者优先]
- 所有的操作会有一个时间戳元数据，副本会对比同步操作的时间戳。 如果大于当前状态时间戳，覆盖掉原来的状态；如果小于当前状态时间戳，则忽略。

### 2P-Set [Two-Phase Set]
- 此模型会维护两个集合，一个是新增集合，保存新增的元素，另一个是删除集合，保存被删除的元素。 模型的最终状态为新增集合和删除集合的**差集**。

> 另外，集合比较特殊，它是只增集合（grow-only set），只能往集合里加元素，不能从集合里移除元素。 这意味着一个元素如果被删除了，就再也不能添加回来。
> 所以删除集合也被叫做 tombstone set（墓碑集合）。 
> 2P-Set 也算是一种 RW-Set（删除优先），特别的点在于元素被删除后不能新增回来。

### G-Counter [Grow-only Counter，只增计数器，一个只能增加计数的计数器]
- 此模型使用 n 个节点的容器（一个整数数组），每个副本会分配一个 id，某个副本给计数器 +1，其实就会给对应的数组元素 +1。 计数器的值为数组的求和。

### PN-Counter [Positive-Negative Counter，一个支持增减的计数器]
- 维护两个G-Counter，一增一减。
> 功能点：比如点赞，喜欢，收藏数

- 多个 CRDT 可以组合成一个更复杂的 CRDT。 类似 G-Counter，但 PN-Counter 使用两个 G-Counter，一个保存新增数（新增操作），另一个保存减少数（减少操作）。 计数器的值为新增数组求和减去减少数组的和。

## 实践
### Yjs 体验
- 多开 https://y-quill.stackblitz.io， 可以感受协同编辑编辑。
- https://github.com/yjs/yjs-demos

## refer
- [CRDT 框架 - Yjs](https://github.com/yjs/yjs)
- [CRDT 实现理论](https://crdt.tech/implementations)
- [基于CRDT实现思维导图协同](https://juejin.cn/post/7245176801491451965)
- [这一次，彻底搞懵 CRDT](https://cloud.tencent.com/developer/article/2376427)