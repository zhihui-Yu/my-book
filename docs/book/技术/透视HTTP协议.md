## 透视HTTP协议

--- 
> 贴图为敬

![HTTP 全图](https://raw.githubusercontent.com/zhihui-Yu/images/main/透视HTTP协议/http-1.png)

### HTTP 历史
- HTTP 协议始于三十年前蒂姆·伯纳斯 - 李的一篇论文；
- HTTP/0.9 是个简单的文本协议，只能获取文本资源；
- HTTP/1.0 确立了大部分现在使用的技术，但它不是正式标准；
- HTTP/1.1 是目前互联网上使用最广泛的协议，功能也非常完善；
- HTTP/2 基于 Google 的 SPDY 协议，注重性能改善，但还未普及；
- HTTP/3 基于 Google 的 QUIC 协议，是将来的发展方向。

### 协议模型
- TCP/IP 网络分层模型 (实际应用场景)
    - 链接层: 负责在以太网、WiFi 这样的底层网络上发送原始数据包 (网卡工作区域，MAC 层)
    - 网际层: IP 协议层，用 IP 地址取代 MAC 地址
    - 传输层: 这个层次协议的职责是保证数据在 IP 地址标记的两点之间"可靠"地传输 (TCP/UDP 层)
    - 应用层: 面向应用，协议有 Telnet、SSH、FTP、SMTP、HTTP
    > TCP 要先建立连接，UDP不需要。
    > TCP 的数据是连续的“字节流”，有先后顺序，而 UDP 则是分散的小数据包，是顺序发，乱序收.
 
- OSI 网络分层模型 (国际标准组织推出)
  - 第一层：物理层，网络的物理形式，例如电缆、光纤、网卡、集线器等等；
  - 第二层：数据链路层，它基本相当于 TCP/IP 的链接层；
  - 第三层：网络层，相当于 TCP/IP 里的网际层；
  - 第四层：传输层，相当于 TCP/IP 里的传输层；
  - 第五层：会话层，维护网络中的连接状态，即保持会话和同步；
  - 第六层：表示层，把数据转换为合适、可理解的语法和语义；
  - 第七层：应用层，面向具体的应用传输数据。

- 两个模型的对应关系
  - 第一层：物理层，TCP/IP 里无对应；
  - 第二层：数据链路层，对应 TCP/IP 的链接层；
  - 第三层：网络层，对应 TCP/IP 的网际层；
  - 第四层：传输层，对应 TCP/IP 的传输层；
  - 第五、六、七层：统一对应到 TCP/IP 的应用层。

 文件传输过程：
  ![HTTP 全图](https://raw.githubusercontent.com/zhihui-Yu/images/main/透视HTTP协议/http-2.png)

### HTTP 报文
> 以下是 TCP 请求的报文结构
- 一个 20 字节的头部数据（存储 TCP 协议必须的额外信息，例如发送方的端口号、接收方的端口号、包序号、标志位等等） + 实际请求的数据
- HTTP 协议的请求报文和响应报文的结构基本相同，由三大部分组成：
  - 起始行（start line）：描述请求或响应的基本信息
    - 请求报文中：
      - 请求方法：是一个动词，如 GET/POST，表示对资源的操作；
      - 请求目标：通常是一个 URI，标记了请求方法要操作的资源；
      - 版本号：表示报文使用的 HTTP 协议版本。
    - 响应报文中：
      - 版本号：表示报文使用的 HTTP 协议版本；
      - 状态码：一个三位数，用代码的形式表示处理的结果，比如 200 是成功，500 是服务器错误；
      - 原因：作为数字状态码补充，是更详细的解释文字，帮助人理解原因。
    > 每个之间有个空格， 结尾有换行
  - 头部字段集合（header）：使用 key-value 形式更详细地说明报文：
    - 头部字段是 key-value 的形式，key 和 value 之间用“:”分隔，最后用 CRLF 换行表示字段结束。比如在“Host: 127.0.0.1”
    > 注意事项：<br/>
      (1) key 不能用'-' 或者空格. <br/>
      (2) 字段后的":"与key之间不能有空格。<br/> 
      (3) 顺序不影响请求。<br/>
    
  - 消息正文（entity）：实际传输的数据，它不一定是纯文本，可以是图片、视频等二进制数据。
  
  >  header 之后必须要有一个“空行”, 也就是“CRLF”，十六进制的“0D0A”。


![HTTP 全图](https://raw.githubusercontent.com/zhihui-Yu/images/main/透视HTTP协议/http-3.png)
![HTTP 全图](https://raw.githubusercontent.com/zhihui-Yu/images/main/透视HTTP协议/http-4.png)
![HTTP 全图](https://raw.githubusercontent.com/zhihui-Yu/images/main/透视HTTP协议/http-6.png)
![HTTP 全图](https://raw.githubusercontent.com/zhihui-Yu/images/main/透视HTTP协议/http-7.png)

报文截图：
![HTTP 全图](https://raw.githubusercontent.com/zhihui-Yu/images/main/透视HTTP协议/http-5.png)


### HTTP 状态码
- 状态行返回的状态码有如下几种：
  - 1××：提示信息，表示目前是协议处理的中间状态，还需要后续的操作；
  - 2××：成功，报文已经收到并被正确处理；
  - 3××：重定向，资源位置发生变动，需要客户端重新发送请求；
  - 4××：客户端错误，请求报文有误，服务器无法处理；
  - 5××：服务器错误，服务器在处理请求时内部发生了错误。

### HTTP 优缺点
- HTTP 最大的优点是简单、灵活和易于扩展；
- HTTP 拥有成熟的软硬件环境，应用的非常广泛，是互联网的基础设施；
- HTTP 是无状态的，可以轻松实现集群化，扩展性能，但有时也需要用 Cookie 技术来实现“有状态”；
- HTTP 是明文传输，数据完全肉眼可见，能够方便地研究分析，但也容易被窃听；
- HTTP 是不安全的，无法验证通信双方的身份，也不能判断报文是否被窜改；
- HTTP 的性能不算差，但不完全适应现在的互联网，还有很大的提升空间。

### HTTP 应用
> gzip: on -> 代表开启压缩，但是只对文本压缩友好，其他类型效果不佳。 <br/>
> 头部字段是协议的一种体现，但是也容易被篡改。 <br/>
> HTTP 默认端口 80 <br/>

#### 连接
- **长连接**: 连接长时间保持，不需要在一次请求后就关闭连接，适合长时间交互。 
    > 在header添加 Connection: keep-alive, nginx中可配置连接时常,   <br>
      Connection: close 意味着关闭连接。<br>
      Connection: Upgrade 意味从 HTTP 切换到 WebSocket<br>
- **短连接**: 每次请求都会三次握手四次挥手, 适合一次性交互。

- 长连接可能导致**队头阻塞**: 长连接中的第一个请求没成功，后面的请求就不能进行。
- 解决方案: 数量解决质量(治标不治本)，多开几个长连接(**并发连接**)，**域名分片**(多个域名指向同一个机器)。 -> **可能连接过多导致拒绝服务**

#### 重定向
> 重定向的header 会有一个 Location: xxx, 代表重定向地址 <br>
> 可以添加Refresh 5; url:xxx 定义多久后重新到哪里， 默认秒
- 300 重定向，会返回多个链接由用户选择
- 301 永久重定向，用于换服务器等
- 302 暂时重定向，用户分流等

#### cookie
> 为了让HTTP有记忆而延申的一种浏览器扩展， 关闭浏览器则cookie失效，总大小默认4K

- 响应报文使用 Set-Cookie 字段发送“key=value”形式的 Cookie 值
- 请求报文里用 Cookie 字段发送多个 Cookie 值
- 为了保护 Cookie，还要给它设置有效期、作用域等属性，常用的有 Max-Age、Expires、Domain、HttpOnly 等
- Max-Age、Expires 设置过期时间，可以同时出现，但前者优先级更高，如果有一个过期则过期。

#### cache
> 为减少HTTP请求，浏览器可以缓存HTTP报文，从而让后面的请求走缓存而不是在次发起HTTP请求。 <必须要添加额外的请求头>

- 在请求头添加 `Cache-Control: max-age=30` # 代表这个页面只能缓存 30 秒，之后就算是过期，不能用
- 如果值为 `no_store` # 不允许缓存
- 如果值为 `no_cache` # 可以用缓存，但是使用前必须去服务器校验时候有新版本
- 如果值为 `must-revalidate` # 没过期就能一直用，过期了再去校验
<br/>

资源校验中条件请求的 5 个头字段：
- if-Modified-Since：是否从某段时间开始后被修改
- If-None-Match：是否有符合的 ETag
- Last-modified： 文件的最后修改时间
- ETag： 实体标签，资源的一个唯一标识

  > (1) 强制刷新默认不走缓存的，因为请求时候会发 Cache-Control: no-cache <br/>
  > (2) 如果资源没有被改变，则返回 304 (NOT MODIFIED), 否则返回资源

#### 代理
> 存在于客户端和服务端之间的一层，一般用于代理服务端，以便做一些负载均衡，安全校验，数据过滤等。
- 头部字段中 X-Forwarded-For： （为谁转发,）代表请求方的 IP 地址 
- 标准是用Via, 含义和 X-Forwarded-For 一样。
- 代理可以缓存一些数据，以便加快客户端的访问速度，但也可以通过一些请求头命令让代理不做缓存.
- Cache-Control: private[public], max-age=5,s-maxage=10 # s-maxage 代理上数据存活时间
- 代理缓存中多了两个字段 
  - max-stale 过期后多久还是可以接受的 
  - min-fresh 最小有效期是多少

#### 大文件的传输
大文件的传输应该使用分段传输。
  - MIME Type = **`multipart/byteranges`**
  - 响应头中包含 **`Accept-Ranges: bytes`** # 说明支持范围请求
  - 响应头加入 **`Transfer-Encoding: chunked`** # 说明是分段数据，并且会自动解码， 如果是Content-Encoding 则需要自行解码
  - 成功返回 **206** Partial Content

    > 像视频的前进后退，也是分段传输的一种体现。 可以多开几个线程，每个线程都请求一段数据，这样就加快了传输速度。<br/>

### HTTPS
- 因为 HTTP 是明文传输，所以不安全，容易被黑客窃听或窜改；
- 通信安全必须同时具备机密性、完整性，身份认证和不可否认这四个特性；
- HTTPS 的语法、语义仍然是 HTTP，但把下层的协议由 TCP/IP 换成了 SSL/TLS；
- SSL/TLS 是信息安全领域中的权威标准，采用多种先进的加密技术保证通信安全；
- OpenSSL 是著名的开源密码学工具包，是 SSL/TLS 的具体实现。

#### HTTPS 的 S 之 SSL/TLS

#### 密码安全学
- 对称加密：一个锁两把钥匙，常用的是 AES 和 ChaCha20
- 非对称加密： 钥匙AB，A加密内容X，只能由B解密得出X，反之亦然。常见的是 RSA 和 ECC
- 摘要算法： 把任意长度的数据“压缩”成固定长度、而且独一无二的“摘要”字符串。常见 MD5、SHA-1
> 哈希消息认证码（HMAC）: 明文数据+摘要+会话密钥加密传输，解密时用会话密钥解密，得出的摘要数据与自己本身的摘要数据对比。相同就是同一个人。
- 签名：用私钥加密数据，则是签名，因为只有公钥才能解密出数据。
- 验签：用公钥解密数据，判断数据是否一致，一致则是验签。
- 由于私钥和公钥的安全性，所以产生CA来统一管理证书。CA也是树级关系，root CA下有多个代理CA，代理下还有代理。

#### TLS 1.2 和 TLS 1.3 的区别
> 获取最终密钥前都是用明文交互
- TLS 1.2连接过程
    - TCP三次握手
    - 浏览器会首先发一个“Client Hello”消息，也就是跟服务器“打招呼”。里面有客户端的版本号、支持的密码套件，还有一个随机数（Client Random），用于后续生成会话密钥。
    - 服务器收到“Client Hello”后，会返回一个“Server Hello”消息。把版本号对一下，也给出一个随机数（Server Random），然后从客户端的列表里选一个作为本次通信使用的密码套件
    - 服务器为了证明自己的身份，就把证书也发给了客户端, 客户端回去CA验证证书有效性
    - 服务器会在证书后发送“Server Key Exchange”消息，里面是椭圆曲线的公钥（Server Params），用来实现密钥交换算法，再加上自己的私钥签名认证。
    - 服务器Server Hello Done　(第一个往返结束)
    - 客户端按照密码套件的要求，也生成一个椭圆曲线的公钥（Client Params），用“Client Key Exchange”消息发给服务器。
    - 现在两边都有Client Params、Server Params，就用密钥加密算法算出一个Pre-Master
    - 用　Client Random、Server Random 和 Pre-Master　加密后生成堆成加密密钥　Master Secret，当成会话密钥，进行通信
    - 客户端发一个“Change Cipher Spec”，然后再发一个“Finished”消息，把之前所有发送的数据做个摘要，再加密一下，让服务器做个验证。　(校验密钥正确性)
    - 服务器也是同样的操作，发“Change Cipher Spec”和“Finished”消息，双方都验证加密解密 OK，握手正式结束，后面就收发被加密的 HTTP 请求和响应了。
- TLS 1.3连接过程
    > 1.3 的密码套件减少了， hello时候会发送 “supported_versions” 表示这是 TLS1.3，“supported_groups”是支持的曲线，“key_share”是曲线对应的参数。
  - 浏览器首先还是发一个“Client Hello”，也就是跟服务器“打招呼”。里面有客户端的版本号、支持的密码套件，还有一个随机数（Client Random）
  - 服务器收到“Client Hello”同样返回“Server Hello”消息，还是要给出一个随机数（Server Random）和选定密码套件。 (会用私钥加密密钥计算的参数)
  - 这时两边都有 Client Random和Server Random、Client Params和Server Params，就可以算出会话密钥了。
  - 在算出主密钥后，服务器立刻发出“Change Cipher Spec”消息。
  - 这两个“Hello”消息之后，客户端验证服务器证书，再发“Finished”消息，就正式完成了握手。
> 少了 Key Exchange 的来回时间，并且把计算所需的都在第一次hello时候返回了，所以速度就快了很多。

#### HTTPS 加速
- 硬件优化： SSL加速器，更好的CPU...
- 软件优化： 挖掘协议的潜力，使用更高级的OpenSSL或者Nginx...
- 协议优化： 协议之间的加密套件，使用简单而安全的，如TLS1.3，椭圆曲线也要选择高性能的曲线，最好是 x25519，次优选择是 P-256
- 证书优化： 
  - OCSP（在线证书状态协议，Online Certificate Status Protocol），向 CA 发送查询请求，让 CA 返回证书的有效状态
  - “OCSP Stapling”（OCSP 装订），它可以让服务器预先访问 CA 获取 OCSP 响应，然后在握手时随着证书一起发给客户端，免去了客户端连接 CA 服务器查询的时间。
- 会话复用
  - Session ID：客户端连接时，发送一个ID，服务器如果找到ID对应的主密钥，就省去了握手的过程
  - Session Ticket： 客户端使用扩展“session_ticket”发送“Ticket”，服务器解密后验证有效期，就可以恢复通信了。 (要使用一个固定的密钥文件（ticket_key）来加密 Ticket，需要定时更换)

#### 申请证书时注意事项
- 第一，申请证书时应当同时申请 RSA 和 ECDSA 两种证书，在 Nginx 里配置成双证书验证，这样服务器可以自动选择快速的椭圆曲线证书，同时也兼容只支持 RSA 的客户端。
- 第二，如果申请 RSA 证书，私钥至少要 2048 位，摘要算法应该选用 SHA-2，例如 SHA256、SHA384 等。
- 第三，出于安全的考虑，“Let’s Encrypt”证书的有效期很短，只有 90 天，时间一到就会过期失效，所以必须要定期更新。你可以在 crontab 里加个每周或每月任务，发送更新请求，不过很多 ACME 客户端会自动添加这样的定期任务，完全不用你操心。

#### HTTP/2
- HTTP   -> HTTP + TCP + IP + MAC 
- HTTP/1 -> HTTP + SSL/TLS + TCP + IP + MAC
- HTTP/2 -> HTTP + TLS(1.2+) + HPack + Stream + TCP + IP + MAC (HPack 请求头压缩算法，Stream 多路复用)
- HTTP/2 请求中，会先发一个控制帧，然后 B/S 既可以交互了，由于可以并发收发数据帧，所以数据帧有流标识，说明帧是哪个流的，而且还有顺序标识，以便重组。 (帧通常不超过 16K，最大是 16M)


> HTTP/3 -> HTTP + TLS(1.2+) + HPack + Stream + iQUIC + UDP + IP + MAC, QUIC <br/>
> 使用UDP 解决头部阻塞问题， QUIC使用包和帧为基本传输单位，并且包中包含流标识，目标地址以及源地址。
> TCP 在丢包后，需要等待新包才能组装数据，这个过程就是头部阻塞以及时间消耗


### NGINX 之 epoll
- nginx的高并发源于使用epoll监听事件，而不用去自己轮询发现事件是否变化。 nginx也是用一个主线程+线程池的方式实现对请求的处理。
- linux中的三个事件处理机制
  - select：使用fd_set结构体告诉内核同时监控那些文件句柄，使用逐个排查方式去检查是否有文件句柄就绪或者超时。该方式有以下缺点：文件句柄数量是有上线的，逐个检查吞吐量低，每次调用都要重复初始化fd_set。
  - poll：该方式主要解决了select方式的2个缺点，文件句柄上限问题(链表方式存储)以及重复初始化问题(不同字段标注关注事件和发生事件)，但是逐个去检查文件句柄是否就绪的问题仍然没有解决。
  - epoll：只对发生变化的文件句柄感兴趣。其工作机制是，使用"事件"的就绪通知方式，通过epoll_ctl注册文件描述符fd，一旦该fd就绪，内核就会采用类似callback的回调机制来激活该fd, epoll_wait便可以收到通知, 并通知应用程序。而且epoll使用一个文件描述符管理多个描述符,将用户进程的文件描述符的事件存放到内核的一个事件表中, 这样数据只需要从内核缓存空间拷贝一次到用户进程地址空间。而且epoll是通过内核与用户空间共享内存方式来实现事件就绪消息传递的，其效率非常高。但是epoll是依赖系统的(Linux)。
> OpenResty (Lua 编写) 的诞生是由于 Nginx 不能进行热配置，每次修改后都要重启。 <br/>
> 而后 Nginx 也开发了一些相关功能。

### WAF (Web Application Firewall： 防火墙)
> 工作在第七层，可以看见整个网络请求，从而可以设置更加精细的策略。
- 常见的攻击有： DDoS(distributed denial-of-service attack), 注入攻击 (代码注入,sql注入,请求头注入)
- ModSecurity 是一个开源的、生产级的 WAF 产品，核心组成部分是“规则引擎”和“规则集”，两者的关系有点像杀毒引擎和病毒特征库；
- WAF 实质上是模式匹配与数据过滤，所以会消耗 CPU，增加一些计算成本，降低服务能力，使用时需要在安全与性能之间找到一个“平衡点”。

### CDN (内容分发网络)
- 为提高访问效率而延申的东西，由于请求需要解析源地址等，加了CDN后，由CDN的服务找到最近的地址给你，这样就节省了很多时间。

### Websocket
> 不同于HTTP的半双工，Websocket是全双工的，解决了数据实时推送的问题，使用独有ws、wss 协议，wss相当于https。
- Sec-WebSocket-Key：一个 Base64 编码的 16 字节随机数，作为简单的认证密钥
- Sec-WebSocket-Version：协议的版本号
- Sec-WebSocket-Accept: 响应报文中的，用于验证客户端请求报文，同样也是为了防止误连接。

### 性能优化
- 性能优化是一个复杂的概念，在 HTTP 里可以分解为服务器性能优化、客户端性能优化和传输链路优化；
- 服务器有三个主要的性能指标：吞吐量、并发数和响应时间，此外还需要考虑资源利用率；
- 客户端的基本性能指标是延迟，影响因素有地理距离、带宽、DNS 查询、TCP 握手等；

- 开源：尽量挖掘服务器自身的潜力，如协议，加密方式，连接等。 (后端应该选用高性能的 Web 服务器，开启长连接，提升 TCP 的传输效率)
- 节流：压缩请求信息，如头部信息，请求的资源等。 (前端应该启用 gzip、br 压缩，减小文本、图片的体积，尽量少传不必要的头字段)
- 缓存：缓存常用数据，以便加速访问， CDN就是基于缓存做的。

> nginx 不支持 br 压缩， 需要安装第三方模块 ngx_brotli

> 此文总结于 https://learn.lianglianglee.com/专栏/透视HTTP协议