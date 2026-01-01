# 虚拟线程

---


19 新特性，默认关闭
运行： java --source 19 --enable-preview Main.java

以前一个java线程对应一个平台线程，现在多个虚拟线程对应一个平台线程， 虚拟线程提高了吞吐，降低延迟，但是它和其他线程的效果是一样的。

dump 虚拟线程需要使用(但是信息不会跟以前的线程一样多):
`jcmd <pid> Thread.dump_to_file -format=json <file>`

> It does not include object addresses, locks, JNI statistics, heap statistics,
> and other information that appears in traditional thread dumps. Moreover,
> because it might need to list a great many threads, generating a new thread dump does not pause the application.


使用：

```java
// 1
Thread.startVirtualThread(() -> System.out.println("Inside Runnable"));

// 2
Thread virtualThread = Thread.ofVirtual().start(() -> System.out.println("Inside Runnable"));
```

```java
// builder 启动
Runnable runnable = () -> System.out.println("Inside Runnable");

Thread.Builder builder = Thread.ofVirtual().name("JVM-Thread");

Thread t1 = builder.start(runnable); 
Thread t2 = builder.start(runnable);
```


```java
// 线程池启动
try(var executor=Executors.newVirtualThreadPerTaskExecutor()){
    IntStream.range(0,10_000).forEach(i->{
        executor.submit(()->{
            Thread.sleep(Duration.ofSeconds(1));
            return i;
        });
    });
}
```

- 需要考虑没执行完，jvm关闭的情况。