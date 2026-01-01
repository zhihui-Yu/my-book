# Win11 系统问题解决方案

---

`date: 2025-08-12`

## Win11 系统登入时绑定微软邮箱导致用户名欠缺

### 解决思路

```md
-> 解绑当前微软邮箱和用户名
-> 断网离线建立本地账户
-> 设置本地账户为Admin权限
-> 注销当前账户，登入新建的用户
-> 联网绑定微软邮箱
-> 删除旧的用户
```

### 命令步骤

1. 管理员权限打开 cmd 输入：`net user your-username password /add`
    - 有时候离线创建本地用户没效果，只能用命令行。 界面操作：设置 -> 账户 -> 其他用户 -> 添加用户 -> 离线情况下可以创建
2. 打开控制面板 (win -> 输入 control)
3. 进入用户账户 -> 管理其他账户 -> 把刚才加的账户设置成admin权限
4. 电脑注销
5. 选择新账户登入
6. 进入 **设置** -> 账户 -> 登入微软邮箱
7. 打开控制面板 -> 管理其他账户 -> 删除旧的账户

## 快捷修改用户名称

1. Press the **Windows key + R**, type in **‘netplwiz’** or **‘control userpasswords2****’**, and hit the **Enter** key.
2. On the User Accounts menu, select the **account** and click on **Properties**.
3. On the **General** tab in the new window, enter the username you’d like to use from now on.
4. Click on **OK**.## 快捷修改用户名称


## Win11 重启资源管理器

1. cmd -> taskkill /f /im explorer.exe && start explorer.exe
2. Ctrl + Shift + Esc 打开任务管理器 -> 找到名为 “Windows 资源管理器” -> 鼠标右键点击它，选择 “重新启动”

## remote call
1. 远程 win+r -> 输入mstsc  -> ip, name pwd (必须要有pwd)

## ip trace
1. `tracert ip_address`

## 端口占用
- `netstat -aon|findstr "8081"`   #查询占用端口8081的pid
- `tasklist|findstr "9088"`  #查询pid对应的任务列表
- `taskkill /T /F /PID 9088` # 杀掉pid