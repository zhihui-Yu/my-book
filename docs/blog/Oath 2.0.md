## Oath 2.0

OAuth 2.0定义了四种授权方式。

- 授权码模式（authorization code）
- 简化模式（implicit）: 浏览器做认证操作，最后返回token给服务器
- 密码模式（resource owner password credentials）: 客户将账号密码输出，让服务器去认证服务器获取凭证
- 客户端模式（client credentials）: 用户在应用上注册，然后应用以客户端的身份去认证服务器获取凭证

### 授权码模式（authorization code）

流程 (copy from [wx](https://developers.weixin.qq.com/doc/oplatform/Website_App/WeChat_Login/Wechat_Login.html))

![Oath_flow](images\Oath_flow.png)

流程：

1. 用户扫码，应用的后端服务(our site backend service)对微信平台发起一个登入认证，并带上回调地址
2. 微信会在用户微信界面拉起一个授权的界面, 用户点确认后，微信会带上code（expire 10 min defaut）重定向到我们的应用服务
3. 应用的后端服务拿着这个code和在微信上绑定自己应用后获取到的appid, app_secret 去换取 access_token （expire 2 hour defaut）
4. 有了这个access_token 我们就可以访问某些微信的API了



> 由于回调地址可能被篡改，code也就有了被盗的风险，为了获取access_token时候可以断言调用者，所以就需要带上 app_id 和 app_secret 来获取token.

- Q1: 为什么一定要有获取code的流程呢， 不能直接吧app_id, app_secret 带上，一次性获取access_token 吗？

  A: 如果直接将所有信息一次打包好传给认证中心，那出现中间人攻击时(回调时候，DNS欺骗)，等于暴露了所有信息，不安全。code只有一次有效，等于说中间人就算拿到code也时被用了的。

- Q2: 为什么说Oauth 2.0 也不安全呢

  A: 在OAuth 1.0中是反复的对Code和Token进行签名，来保证Token不会被篡改，但是OAuth 2.0中却没有，因为OAuth 2.0是基于Https的，所以如果没有Https的支持OAuth 2.0可能还不如OAuth 1.0。在 OAuth 2.0 中，使用 HTTPS 可以说是必须的，而且 client 有义务验证证书的真假，防止中间人攻击，而 authorization server 和 resource server 都有义务申请可信任的第三方颁发的真实的 SSL 证书。(copy from 星冷 https://www.zhihu.com/question/27446826/answer/2151631244)

- Q3: Oath 1.0 是什么呢



额外小知识：

1. 跨站点请求伪造(CSRF)如何破解：服务器需要校验请求来源，可加Refer 在header，或者在请求后加随机数以便校验时候存在这个随机数。

2. 中间人攻击： 可用本地密钥破解，客户端内嵌公钥，而私钥只有服务端有，这样使用http请求后，中间人破解不了请求数据。