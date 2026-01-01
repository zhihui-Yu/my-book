## chocolatey

---

> link: https://chocolatey.org/

### 介绍
一个方便快捷的window 软件管理工具，能用命令行实现软件安装卸载搜索等功能。

### 安装步骤

> https://docs.chocolatey.org/en-us/choco/setup

- 使用管理员权限打开cmd/powershell
- 执行 `Get-ExecutionPolicy`， 如果是 `Restricted`, 则执行`Set-ExecutionPolicy AllSigned` or `Set-ExecutionPolicy Bypass -Scope Process`.
- 执行安装 `Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))`
- 输入 choco 或者 choco -?， 有choco相关信息就是成功

### choco 命令

> https://docs.chocolatey.org/en-us/choco/commands/

- choco search xx
- choco install xx

### 实践
```shell
choco -v # 显示当前版本
choco search xx # 搜索xx软件
choco install xx # 安装xx软件
choco uninstall xx # 卸载xx软件
```