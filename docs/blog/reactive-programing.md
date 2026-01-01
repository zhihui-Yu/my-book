## Reactive Programming

----

#### why use it?

- 函数式： 东西准备好 -> 算 -> 用
    - 每个执行controller的线程去获取数据，线程数量固定，基于请求量而出现等待
  
  ![bloking](https://raw.githubusercontent.com/zhihui-Yu/images/main/thinking/bloking.png)
  
- 响应式： 东西准备好 -> 用 -> 算 [有背压机制]
    - 执行db操作是额外的线程，不会导致主线程长时间等待。从而提高吞吐量，但是由于额外线程数量有限，所以请求量大时会出现等待，背压效果就出来了。
    ![no-blocking](https://raw.githubusercontent.com/zhihui-Yu/images/main/thinking/no-blocking.png)

> images copy from https://medium.com/@ijayakantha/reactive-programming-welcome-to-high-performance-non-blocking-api-development-b806180ca150