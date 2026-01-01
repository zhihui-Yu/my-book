# Java 知识点

---

## IO

- BIO：单线程处理所有请求
- NIO：一个线程池处理accept， 一个线程池处理read/write并处理读写后相关逻辑
- AIO：一个线程池处理accept， 一个线程池处理read/write并submit个新线程处理读写后的相关逻辑

## AtomicInteger/AtomicReference

原理：

- 通过Unsafe 类型进行自旋+ CAS （compare and set） 操作
- 内部维护一个指针，在进行CAS时候，由于是汇编指令，获取地址并比较数值然后设置新值，所以是原子级别的。
- 自旋就是do while去调用CAS （jdk.internal.misc.Unsafe.getAndAddInt）
- 三种问题：
    - 可能出现长时间的自旋
    - 只能用一个变量，或者一个对象。
    - 会出现ABA问题
        - AtomicStampedReference 不会ABA，因为内部存储了一个版本号 stamp。

## Calendar使用

1. `Calendar calendar = Calendar.getInstance(); calendar.get(Calendar.XXX);`
2. 要注意每个参数的定义，月从0开始算的，星期是从周日(1)开始算的

## BigDecimal 精度问题：

`System.out.println(new BigDecimal(0.99)); // 0.9899999999999999911182158029987476766109466552734375`
`System.out.println(BigDecimal.valueOf(0.99d)); // 0.99`

- 原因：第一种时二进制转十进制导致精度问题，第二种转为string再去转BigDecimal

## @HotSpotIntrinsicCandidate注解

- 这个注解允许HotSpot VM自己来写汇编或IR编译器来实现该方法以提供性能。
  也就是说虽然外面看到的在JDK9中weakCompareAndSet和compareAndSet底层依旧是调用了一样的代码，但是不排除HotSpot
  VM会手动来实现weakCompareAndSet真正含义的功能的可能性。

## 反编译

<pre>
javap -c HelloWorld.class -- 反编译
javap -c verbose HelloWorld.class -- 输出附加信息
反编译后的指令集：
初始化对象
- new 占三位，创建对象
- dup 复制栈顶引用值
- invokespecial 执行对象初始化
  存储变量：
- astore_1
  加载变量到栈
- aload_1
</pre>

## JVM GC

GC 分为

1. Yong 区 (一般数据创建了都放里面) 会频繁发送 minor GC
2. Old 区 (大对象或者经历15次minor GC后仍然存在的对象)， 存放不下时会 Full GC
3. Perm 区 基本不动 (可以说时"永久代")

GC 算法：

1. 引用计数法(因无法处理循环引用已淘汰)
   > 对每个对象都要有一个引用计数器，耗性能
2. 复制算法 (年轻代中使用的)
   > 优点： 直接拷贝存活的对象然后清空原来的区域，没有内存碎片 (空的且可能无法被使用的空间)
   缺点： 需要双倍的空间
3. 标记清除 (老年代的)
   > 优点： 不需要额外的空间
   缺点： 需要进行两次扫描，一次标记，一次清除。还有内存碎片
4. 标记压缩 (老年代)
   > 优点：没有内存碎片
   缺点：需要两次扫描和移动对象的成本。
5. 标记清除压缩
   > 标记清除和标记压缩的混合版，只有多次GC后才进行压缩，减少了移动对象的成本。

## SQL 注入

预编译需要数据库支持预编译才行。 在 ClientPreparedStatement executeQuery() 中有chekDML，判断sql中是否有非法字符。

1. 使用PreparedStatement，在执行语句前，
2. 先将sql传给mysql做一次prepare，
3. 然后再校验参数中的非法字符，有不合法的就会报异常，
4. 然后传给 mysql 参数，执行之前的prepare 语句。

## static 修饰作用

- 在类内部使用，既表明：这个方法、变量在加载实例前就被加载了，既类变量、类方法的含义。
- 如果是静态内部类，则可以脱离外部类生存，声明时不需要 new Out().new Inner(), 只需要 new Out.Inner();

## 如果类变量和局部变量重名，会怎么样

- 如果类变量和局部变量重名，则进行就近原则。

## 地址引用

- String 和 包装类( Integer/ Double...) 是地址引用。

<pre>
   Integer i = 100;
   change(i); // 在change中修改i的值，change 方法内修改了i的值，只是在常量池内声明一个值并把引用地址给方法内的i，不影响外部。
   // i 这是还是100， 因为无论在change中如何修改，都不影响i的值.
   执行方法是在栈中的，每个方法都是独立的。
</pre>