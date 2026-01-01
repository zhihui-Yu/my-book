# Nginx

---

> download: https://nginx.org/en/download.html

## win: 解压后进去文件夹 -> start nginx -> nginx -s quit[/stop]
异常: 如果没有pid文件，只能手动kill进程 [windows 在详细信息可见]

## 负载均衡策略：
1. 轮询（默认）每个请求按时间顺序逐一分配到不同的后端服务器，如果后端服务器down掉，能自动剔除。
<pre>
   upstream backserver {
       server 192.168.0.14;
       server 192.168.0.15;
   }
</pre>
2. weight. 指定轮询几率，weight和访问比率成正比，用于后端服务器性能不均的情况。
<pre>
   upstream backserver {
       server 192.168.0.14 weight=3;
       server 192.168.0.15 weight=7;
   }
</pre>
3. ip_hash. 通过ip的hash定位到一台可能有用户登入信息的服务器。
<pre>
   upstream backserver {
       ip_hash;
       server 192.168.0.14:88;
       server 192.168.0.15:80;
   }
</pre>
4. fair（第三方）按后端服务器的响应时间来分配请求，响应时间短的优先分配。
<pre>
   upstream backserver {
       server server1;
       server server2;
       fair;
   }
</pre>
5. url_hash（第三方）按访问url的hash结果来分配请求，使每个url定向到同一个（对应的）后端服务器，后端服务器为缓存时比较有效。
<pre>
   upstream backserver {
       server squid1:3128;
       server squid2:3128;
       hash $request_uri;
       hash_method crc32;
   }
</pre>

### 实例一：
<pre>
  proxy_pass http://backserver/;
  upstream backserver{
      ip_hash;
      server 127.0.0.1:9090 down; (down 表示单前的server暂时不参与负载)
      server 127.0.0.1:8080 weight=2; (weight 默认为1.weight越大，负载的权重就越大)
      server 127.0.0.1:6060;
      server 127.0.0.1:7070 backup; (其它所有的非backup机器down或者忙的时候，请求backup机器)
  }
</pre>
> max_fails ：允许请求失败的次数默认为1.当超过最大次数时，返回proxy_next_upstream 模块定义的错误
fail_timeout:max_fails次失败后，暂停的时间

配置示例：

<pre>
#user  nobody;
  worker_processes  4;
  events {
      # 最大并发数
      worker_connections  1024;
  }
  http{
      # 待选服务器列表
      upstream myproject{
          # ip_hash指令，将同一用户引入同一服务器。
          ip_hash;
          server 125.219.42.4 fail_timeout=60s;
          server 172.31.2.183;
      }

      server{
          # 监听端口
          listen 80;
          # 监听的地址, 用localhost好像有点问题
          server 127.0.0.1

          # 根目录下
          location / {
          # 选择哪个服务器列表
              proxy_pass http://myproject;
          }

      }
  }
</pre>
