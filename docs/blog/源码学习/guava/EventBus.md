## EventBus 源码分析
---

### 如何使用

案列如下

添加maven依赖
```text
<dependency>
    <groupId>com.google.guava</groupId>
    <artifactId>guava</artifactId>
    <version>31.0.1-jre</version>
</dependency>
```

```java
public class EventBusExample {
    public static final String key = "KEY";

    public static void main(String[] args) {
        EventBus eventBus = new EventBus(key);
        eventBus.register(new SubscribeOne());
        eventBus.register(new SubscribeTwo());
        eventBus.post(new EventOne());
        eventBus.post(new EventTwo());
    }

    public static class SubscribeOne {
        @Subscribe
        public void handle(EventOne event) {
            System.out.println("one: " + event.msg + "," + event.value);
        }

        public void handle2(EventOne event) {
            System.out.println("one: " + event.msg + "," + event.value);
        }
    }

    public static class SubscribeTwo {
        @Subscribe
        public void handle(EventTwo event) {
            System.out.println("two: " + event.msg + "," + event.value);
        }

        public void handle2(EventTwo event) {
            System.out.println("two: " + event.msg + "," + event.value);
        }
    }

    public static abstract class Event {
        public String msg;

        public Event() {
            this("Hello World!");
        }

        public Event(String msg) {
            this.msg = msg;
        }
    }

    public static class EventOne extends Event {
        public final String value = "one-msg";

        public EventOne() {
            super("one");
        }
    }

    public static class EventTwo extends Event {
        public final String value = "two-msg";

        public EventTwo() {
            super("two");
        }
    }
}
```

执行结果：

```text
one: one,one-msg
two: two,two-msg
```

### 分析

从上面可以发现如下：

1. 订阅者会判断消息的类型
2. 只有加了@Subscribe注解的方法才会被认为是消息消费时候的方法。
3. 每个订阅者消费时候是相互隔离的(其中一个消费出问题，不影响其他订阅者)

那EventBus是怎么做到的呢？

### 源码

先看 EventBus 的成员变量

```java
public class EventBus {
    private final String identifier; // 可以认为是 event bus 唯一标识
    private final Executor executor; // 默认 MoreExecutors.directExecutor()，
    private final SubscriberExceptionHandler exceptionHandler; // 订阅者处理出现异常时候执行 默认 LoggingHandler.INSTANCE， 可配置
    private final SubscriberRegistry subscribers = new SubscriberRegistry(this);
    private final Dispatcher dispatcher; // 事件分发处理器 默认 Dispatcher.perThreadDispatchQueue() 保证所有消息有序性
}
```

再看调用register时候发生了什么

```java
// 为格式好看加了个类名，请忽略这个
public class Analyze {
    
    // EventBus 中的 register方法
    public void register(Object object) {
        subscribers.register(object); // 调用了订阅注册器的注册方法
    }

    // 订阅注册器的register方式如下
    void register(Object listener) {
        // 通过反射找到类中所有方法，并选出有标记 @Subscribe 的方法组装成 Subscriber(这步中有些巧妙之处后面说)
        // 这里使用 Multimap, 所以返回的可能是 Map<方法首参类型(方法只能有一个参数),Collection<Subscriber>>
        Multimap<Class<?>, Subscriber> listenerMethods = findAllSubscribers(listener);

        for (Entry<Class<?>, Collection<Subscriber>> entry : listenerMethods.asMap().entrySet()) {
            Class<?> eventType = entry.getKey();
            Collection<Subscriber> eventMethodsInListener = entry.getValue();

            // 获取这中类型的当前所有的 Subscriber 列表
            CopyOnWriteArraySet<Subscriber> eventSubscribers = subscribers.get(eventType);

            // 下面就是把 listener 类中所有的当前类型的 Subscribe 都加入 subscribers 集合中
            if (eventSubscribers == null) {
                CopyOnWriteArraySet<Subscriber> newSet = new CopyOnWriteArraySet<>();
                eventSubscribers =
                    MoreObjects.firstNonNull(subscribers.putIfAbsent(eventType, newSet), newSet);
            }

            eventSubscribers.addAll(eventMethodsInListener);
        }
    }
}
```

知道了怎么注册，那来看看一个 event 如何给分发给相应的 Subscribers

```java
// 为格式好看加了个类名，请忽略这个
public class Analyze {
    
    // EventBus 中的 post 方法
    public void post(Object event) {
        Iterator<Subscriber> eventSubscribers = subscribers.getSubscribers(event);
        if (eventSubscribers.hasNext()) {
            // 交给 事件分发处理器 分发给每个订阅者
            dispatcher.dispatch(event, eventSubscribers);
        } else if (!(event instanceof DeadEvent)) {
            // the event had no subscribers and was not itself a DeadEvent
            post(new DeadEvent(this, event));
        }
    }


    // 前提知识： 
    //     1. queue : ThreadLocal<Queue<Event>>
    //     2. dispatching : ThreadLocal<Boolean> 

    // 这个方法保证同一线程内消息的顺序性
    @Override
    void dispatch(Object event, Iterator<Subscriber> subscribers) {
        checkNotNull(event);
        checkNotNull(subscribers);
        Queue<Event> queueForThread = queue.get();
        // 将当前请求插入该线程中的处理队列末
        queueForThread.offer(new Event(event, subscribers));

        if (!dispatching.get()) {
            // 保证该线程的队列是顺序消费
            dispatching.set(true);
            try {
                Event nextEvent;
                while ((nextEvent = queueForThread.poll()) != null) {
                    while (nextEvent.subscribers.hasNext()) {
                        // last
                        nextEvent.subscribers.next().dispatchEvent(nextEvent.event);
                    }
                }
            } finally {
                dispatching.remove();
                queue.remove();
            }
        }
    }

    // last: 最后让每个 subscriber 消费 event
    final void dispatchEvent(final Object event) {
        executor.execute(
            new Runnable() {
                @Override
                public void run() {
                    try {
                        invokeSubscriberMethod(event);
                    } catch (InvocationTargetException e) {
                        // 可配置 SubscriberExceptionHandler
                        bus.handleSubscriberException(e.getCause(), context(event));
                    }
                }
            });
    }

}
```

好了关于 EventBus 的基本流程都知道了，现在让我们来看看它是怎么在 class 中找出带有 @Subscriber 注解的 methods 呢。<br/>
这个是发生在注册时候，findAllSubscribers() 内调用了 getAnnotatedMethods(clazz)

```java
// 为格式好看加了个类名，请忽略这个
public class Analyze {

    private static ImmutableList<Method> getAnnotatedMethods(Class<?> clazz) {
        try {
            // 这里会从本地 cache 取，没有在走 load 方法
            return subscriberMethodsCache.getUnchecked(clazz);
        } catch (UncheckedExecutionException e) {
            throwIfUnchecked(e.getCause());
            throw e;
        }
    }

    // 前提知识：subscriberMethodsCache : LoadingCache<Class<?>, ImmutableList<Method>> 
    // 在build这个 subscriberMethodsCache 对象时， 重写了它的 load() 方法
    private static final LoadingCache<Class<?>, ImmutableList<Method>> subscriberMethodsCache =
        CacheBuilder.newBuilder()
            .weakKeys()
            .build(
                new CacheLoader<Class<?>, ImmutableList<Method>>() {
                    @Override
                    public ImmutableList<Method> load(Class<?> concreteClass) throws Exception {
                        // 找出 @Subscriber 的 method
                        return getAnnotatedMethodsNotCached(concreteClass);
                    }
                });

    private static ImmutableList<Method> getAnnotatedMethodsNotCached(Class<?> clazz) {
        Set<? extends Class<?>> supertypes = TypeToken.of(clazz).getTypes().rawTypes();
        Map<MethodIdentifier, Method> identifiers = Maps.newHashMap();
        for (Class<?> supertype : supertypes) {
            for (Method method : supertype.getDeclaredMethods()) {

                // synthetic总的来说，是由编译器引入的字段、方法、类或其他结构 
                if (method.isAnnotationPresent(Subscribe.class) && !method.isSynthetic()) {
                    // 带有 @Subscribe 注解的方法，有且只能有一个参数
                    Class<?>[] parameterTypes = method.getParameterTypes();
                    checkArgument(
                        parameterTypes.length == 1,
                        "Method %s has @Subscribe annotation but has %s parameters. "
                            + "Subscriber methods must have exactly 1 parameter.",
                        method,
                        parameterTypes.length);

                    // 不接受原始类型的入参 (int, byte, long ...)
                    checkArgument(
                        !parameterTypes[0].isPrimitive(),
                        "@Subscribe method %s's parameter is %s. "
                            + "Subscriber methods cannot accept primitives. "
                            + "Consider changing the parameter to %s.",
                        method,
                        parameterTypes[0].getName(),
                        Primitives.wrap(parameterTypes[0]).getSimpleName());

                    MethodIdentifier ident = new MethodIdentifier(method);
                    if (!identifiers.containsKey(ident)) {
                        identifiers.put(ident, method);
                    }
                }
            }
        }
        return ImmutableList.copyOf(identifiers.values());
    }
}
```

### 总结

1. 有点像本地小型的 kafka 系统一样。
2. 要注意多线程使用时，不能保证消息顺序消费。
3. 观察者模式的使用案列。