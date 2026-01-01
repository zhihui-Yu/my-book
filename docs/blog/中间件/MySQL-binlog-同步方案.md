# MySQL binlog 同步方案

--- 

## 目标
- 使用canal假装成 mysql 的从库，同步 binlog 来对mysql的数据做额外处理[数据同步，清洗更新]

## 步骤

### 安装 MySQL
- 用docker安装 MySQL
```text
docker run -p 3307:3306 --name c_mysql -v C:\work\canal\mysql\log:/var/log/mysql -v C:\work\canal\mysql\data:/var/lib/mysql -v C:\work\canal\mysql\conf:/etc/mysql -v C:\work\canal\mysql\mysql-files:/var/lib/mysql-files -e MYSQL_ROOT_PASSWORD=root -d mysql:8.0.23
```
- 创建canal用户并赋权
```SQL
CREATE USER canal IDENTIFIED BY 'canal'; 
GRANT SELECT, REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'canal'@'%';
FLUSH PRIVILEGES
```
- 查看当前使用的 binlog 文件: `show master status;`
  - 重启会生成新的binlog文件

### 安装 canal
- `docker run --name canal-server -p 11111:11111 -d canal/canal-server:latest`
- `docker cp canal-server:/home/admin/canal-server C:\work\canal\canal-server` # 复制文件夹
- `docker run --name canal-server -p 11111:11111 -v C:\work\canal\canal-server:/home/admin/canal-server -d canal/canal-server:latest` # 映射
- `vi canal-server/conf/example/instance.properties` 修改mysql地址，账号密码，重启canal

<pre>
- 启动失败： exit:139
  - 关闭dokcer
  - 命令行执行 ：wsl --shutdown
  - 在%userprofile%\目录新建 `.wslconfig`，内容如下（不要有空行）：
[wsl2]
kernelCommandLine = vsyscall=emulate
  - 重启即可
- caching_sha2_password Auth failed
  - 修改mysql的登入的身份验证插件
  - `ALTER USER 'canal'@'%' IDENTIFIED WITH mysql_native_password BY 'password';`
</pre>

### 自定义项目接收 dump sql
### 依赖
```maven
<dependency>
    <groupId>com.alibaba.otter</groupId>
    <artifactId>canal.client</artifactId>
    <version>1.1.4</version>
</dependency>
```
### 启动: [official example](https://github.com/alibaba/canal/wiki/ClientExample)
```java

import com.alibaba.otter.canal.client.CanalConnector;
import com.alibaba.otter.canal.client.CanalConnectors;
import com.alibaba.otter.canal.protocol.CanalEntry;
import com.alibaba.otter.canal.protocol.Message;

import java.net.InetSocketAddress;
import java.util.List;

/**
 * <a href="https://developer.aliyun.com/article/770496">refer</a>
 * @author simple
 */

public class CanalClient {
    private final static int BATCH_SIZE = 1000;

    public static void main(String[] args) {
        // 创建链接
        CanalConnector connector = CanalConnectors.newSingleConnector(new InetSocketAddress("127.0.0.1", 11111), "example", "", "");
        try {
            //打开连接
            connector.connect();
            //订阅数据库表,全部表
            connector.subscribe(".*\\..*");
            //回滚到未进行ack的地方，下次fetch的时候，可以从最后一个没有ack的地方开始拿
            connector.rollback();
            while (true) {
                // 获取指定数量的数据
                Message message = connector.getWithoutAck(BATCH_SIZE);
                //获取批量ID
                long batchId = message.getId();
                //获取批量的数量
                int size = message.getEntries().size();
                //如果没有数据
                if (batchId == -1 || size == 0) {
                    try {
                        //线程休眠2秒
                        Thread.sleep(2000);
                    } catch (InterruptedException e) {
                        e.printStackTrace();
                    }
                } else {
                    //如果有数据,处理数据
                    printEntry(message.getEntries());
                }
                //进行 batch id 的确认。确认之后，小于等于此 batchId 的 Message 都会被确认。
                connector.ack(batchId);
            }
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            connector.disconnect();
        }
    }

    /**
     * 打印canal server解析binlog获得的实体类信息
     */
    private static void printEntry(List<CanalEntry.Entry> entrys) {
        for (CanalEntry.Entry entry : entrys) {
            if (entry.getEntryType() == CanalEntry.EntryType.TRANSACTIONBEGIN || entry.getEntryType() == CanalEntry.EntryType.TRANSACTIONEND) {
                //开启/关闭事务的实体类型，跳过
                continue;
            }
            //RowChange对象，包含了一行数据变化的所有特征
            //比如isDdl 是否是ddl变更操作 sql 具体的ddl sql beforeColumns afterColumns 变更前后的数据字段等等
            CanalEntry.RowChange rowChage;
            try {
                rowChage = CanalEntry.RowChange.parseFrom(entry.getStoreValue());
            } catch (Exception e) {
                throw new RuntimeException("ERROR ## parser of eromanga-event has an error , data:" + entry.toString(), e);
            }
            //获取操作类型：insert/update/delete类型
            CanalEntry.EventType eventType = rowChage.getEventType();
            //打印Header信息
            System.out.println(String.format("================ binlog[name: %s, offset: %s] , name[db: %s, table: %s] , eventType : %s =================",
                entry.getHeader().getLogfileName(), entry.getHeader().getLogfileOffset(),
                entry.getHeader().getSchemaName(), entry.getHeader().getTableName(),
                eventType));
            //判断是否是DDL语句
            if (rowChage.getIsDdl()) {
                System.out.println("================ isDdl: true ==============");
                System.out.println("sql:" + rowChage.getSql());
            }
            //获取RowChange对象里的每一行数据，打印出来
            for (CanalEntry.RowData rowData : rowChage.getRowDatasList()) {
                //如果是删除语句
                if (eventType == CanalEntry.EventType.DELETE) {
                    printColumn(rowData.getBeforeColumnsList());
                    //如果是新增语句
                } else if (eventType == CanalEntry.EventType.INSERT) {
                    printColumn(rowData.getAfterColumnsList());
                    //如果是更新的语句
                } else {
                    //变更前的数据
                    System.out.println("------- before ---------");
                    printColumn(rowData.getBeforeColumnsList());
                    //变更后的数据
                    System.out.println("------- after ---------");
                    printColumn(rowData.getAfterColumnsList());
                }
            }
        }
    }

    private static void printColumn(List<CanalEntry.Column> columns) {
        for (CanalEntry.Column column : columns) {
            System.out.print(column.getName() + " : " + column.getValue() + "    update=" + column.getUpdated() + "\t");
        }
        System.out.println();
    }
}
```

## 总结
### 能做什么
- 数据库镜像
- 数据库实时备份
- 索引构建和实时维护
- 业务cache(缓存)刷新
- 带业务逻辑的增量数据处理

### 局限性
- [canal基于binlog同步方案的局限性和思考](http://www.fblinux.com/?p=2331)
  - canal 2023年又开始更新了。 现在版本 [canal-1.1.7]