# FlaskModel
支持高并发tensorflow模型推理的flask web服务部署


## 环境：

​    系统：Ubuntu16.04

​    语言：Python3.6

## 参考：

1. <https://blog.csdn.net/zmy941110/article/details/89639883?utm_medium=distribute.pc_aggpage_search_result.none-task-blog-2~all~first_rank_v2~rank_v25-4-89639883.nonecase&utm_term=%E9%AB%98%E5%B9%B6%E5%8F%91%E9%A1%B9%E7%9B%AE%E9%83%A8%E7%BD%B2&spm=1000.2123.3001.4430>
2. <https://blog.csdn.net/Tilyp/article/details/98943832>
3. <http://liyangliang.me/posts/2015/11/using-celery-with-flask/>
4. <https://liyangliang.me/posts/2016/05/using-celery-with-flask-and-gevent/>
5. <https://www.cnblogs.com/wangkun122/p/11158291.html>
6. <https://www.cnblogs.com/xingxia/p/supervisor_all.html>
7. <https://blog.csdn.net/Lyong19900923/article/details/92762281?utm_medium=distribute.pc_relevant.none-task-blog-BlogCommendFromMachineLearnPai2-2.edu_weight&depth_1-utm_source=distribute.pc_relevant.none-task-blog-BlogCommendFromMachineLearnPai2-2.edu_weight>
8. <https://blog.csdn.net/qq_30835699/article/details/107140909?utm_medium=distribute.pc_aggpage_search_result.none-task-blog-2~all~sobaiduend~default-2-107140909.nonecase&utm_term=%E5%90%88%E5%B9%B6%E5%A4%9A%E4%B8%AArdb%E6%96%87%E4%BB%B6&spm=1000.2123.3001.4430>
9. <https://gitee.com/xinxiangbobby/flask-restful-example>
10. <https://cloud.tencent.com/developer/article/1345460>

## 安装：

安装**redis**：

```shell
sudo apt-get install redis-server
```

安装**Flask，Celery，Redis，Gunicorn， Supervisor**

```SHELL
python -m pip install flask redis celery gunicorn supervisor==4.2.1
```

安装**Nginx**

```shell
sudo apt-get install nginx -y
```

### 1.Redis

**Redis**是现在最受欢迎的NoSQL数据库之一，Redis是一个使用ANSI C编写的开源、包含多种数据结构、支持网络、基于内存、可选持久性的键值对存储数据库，其具备如下特性：

- 基于内存运行，性能高效
- 支持分布式，理论上可以无限扩展
- key-value存储系统
- 开源的使用ANSI C语言编写、遵守BSD协议、支持网络、可基于内存亦可持久化的日志型、Key-Value数据库，并提供多种语言的API

相比于其他数据库类型，Redis具备的特点是：

- C/S通讯模型
- 单进程单线程模型
- 丰富的数据类型
- 操作具有原子性
- 持久化
- 高并发读写
- 支持lua脚本

**Redis** 的应用场景包括：缓存系统（“热点”数据：高频读、低频写）、计数器、消息队列系统、排行榜、社交网络和实时系统。

**本项目中flask任务的结果存储在Redis数据库中，主要手段是通过设置redis作为 celery的broker, backend等，同 redis 中数据记录交互操作**

例如

```python
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'  # 最后的'0'为数据库名称，可自定义。当改成'redis://127.0.0.1:6379/1'后，原先在'redis://127.0.0.1:6379/0'路由中数据集中的结果就无法访问，直到重启服务切回'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'

# broker redis的消息中间件
# backend 存储任务结果
CLASSMODEL = Celery("FlaskModel",
                    broker=CELERY_BROKER_URL,
                    backend=CELERY_RESULT_BACKEND,
                    CELERY_TASK_SERIALIZER='json',
                    )
```



主要过程如下：

```txt
1、当发起一个 task 时，会向 redis 的 celery key 中插入一条记录。
2、如果这时有正在待命的空闲 worker，这个 task 会立即被 worker 领取。
3、如果这时没有空闲的 worker，这个 task 的记录会保留在 celery key 中。
4、这时会将这个 task 的记录从 key celery 中移除，并添加相关信息到 unacked 和 unacked_index 中。
5、worker 根据 task 设定的期望执行时间执行任务，如果接到的不是延时任务或者已经超过了期望时间，则立刻执行。
6、worker 开始执行任务时，通知 redis。（如果设置了 CELERY_ACKS_LATE = True 那么会在任务执行结束时再通知）
7、redis 接到通知后，将 unacked 和 unacked_index 中相关记录移除。
8、如果在接到通知前，worker 中断了，这时 redis 中的 unacked 和 unacked_index 记录会重新回到 celery key 中。(这个回写的操作是由 worker 在 “临死” 前自己完成的，所以在关闭 worker 时为防止任务丢失，请务必使用正确的方法停止它，如: celery multi stop w1 -A proj1)
9、在 celery key 中的 task 可以再次重复上述 2 以下的流程。
10、celery 只是利用 redis 的 list 类型，当作个简单的 Queue，并没有使用消息订阅等功能
```

验证**redis**：

```shell
$redis-cli
127.0.0.1:6379> 
```

如果是用**apt-get**或者**yum install**安装的**redis**，可以直接通过下面的命令停止/启动/重启redis

```shell
sudo /etc/init.d/redis-server stop 
sudo /etc/init.d/redis-server start 
sudo /etc/init.d/redis-server restart
```

如果是通过源码安装的**redis**，则可以通过**redis**的客户端程序**redis-cli**的**shutdown**命令来重启**redis**

**1.redis关闭** 

```shell
redis-cli -h 127.0.0.1 -p 6379 shutdown
```

**2.redis启动** 

```shell
redis-server
```

#### **redis**常用命令

```shell
redis-cli -h ip地址 -p 端口号  # 启动客户端命令:[root@sakura]，由于默认IP是127.0.0.1，端口是6379，我们只需要输入命令redis-cli即可
redis-cli  # 进入数据库
127.0.0.1:6379>  # 进入后显示
127.0.0.1:6379> quit  # 退出
```

Redis支持多个数据库，并且每个数据库的数据是隔离的不能共享，每个数据库对外都是一个从0开始的递增数字命名，Redis默认支持16个数据库（可以通过配置文件支持更多，无上限），可以通过配置databases来修改这一数字。客户端与Redis建立连接后会自动选择0号数据库，不过可以随时使用SELECT命令更换数据库：

```shell
127.0.0.1:6379> SET db_number 0         # 默认使用 0 号数据库
OK
127.0.0.1:6379> SELECT 1                # 使用 1 号数据库
OK
127.0.0.1:6379[1]> GET db_number        # 已经切换到 1 号数据库，注意 Redis 现在的命令提示符多了个 [1]
(nil)
127.0.0.1:6379[1]> SET db_number 1
OK
127.0.0.1:6379[1]> GET db_number        # 因为已经默认为 1 号数据库，所以返回“1”
"1"
```

然而这些以数字命名的数据库又与我们理解的数据库有所区别。首先Redis不支持自定义数据库的名字，每个数据库都以编号命名，开发者必须自己记录哪些数据库存储了哪些数据。另外Redis也不支持为每个数据库设置不同的访问密码，所以一个客户端要么可以访问全部数据库，要么连一个数据库也没有权限访问。最重要的一点是多个数据库之间并不是完全隔离的，比如FLUSHALL命令可以清空一个Redis实例中所有数据库中的数据。综上所述，这些数据库更像是一种命名空间，而不适宜存储不同应用程序的数据。比如可以使用0号数据库存储某个应用生产环境中的数据，使用1号数据库存储测试环境中的数据，但不适宜使用0号数据库存储A应用的数据而使用1号数据库B应用的数据，不同的应用应该使用不同的Redis实例存储数据。由于Redis非常轻量级，一个空Redis实例占用的内在只有1M左右，所以不用担心多个Redis实例会额外占用很多内存。 

Redis是典型的Key-Value类型数据库，Key为字符类型，Value的类型常用的为五种类型：String、Hash 、List 、 Set 、 Ordered Set

简单介绍几种：

##### **赋值**

<https://cloud.tencent.com/developer/article/1345460>

**set key value**:设定key持有指定的字符串value，如果该key存在则进行覆盖操作，总是返回"OK"，如果赋予相同的key，新的value会覆盖老的value

example:

```javascript
127.0.0.1:6379> set username zhangsan
OK
```

##### **取值**

**get key**:获取key的value。如果与该key关联的value不是string类型，redis将返回错误信息，因为get命令只能用于获取string value；如果该key不存在，返回nil

example:

```javascript
127.0.0.1:6379> get username
"zhangsan"
```

##### **删除**

**del key**:删除指定key，返回值是数字类型，表示删了几条数据

example:

```javascript
127.0.0.1:6379> del username
(integer) 1
```

**删除所有Key**

```shell
flushdb  # 删除当前数据库中的所有Key
flushall # 删除所有数据库中的key
```

#### 关于连接池

CPU 不是 Redis 的瓶颈。Redis 的瓶颈最有可能是机器内存或者网络带宽。（以上主要来自官方 FAQ）既然单线程容易实现，而且 CPU 不会成为瓶颈，那就顺理成章地采用单线程的方案了。关于 redis 的性能，官方网站也有，普通笔记本轻松处理每秒几十万的请求。

Redis 是单进程单线程的，它利用队列技术将并发访问变为串行访问，消除了传统数据库串行控制的开销。

Redis 是基于内存的数据库，使用之前需要建立连接，建立断开连接需要消耗大量的时间。

再假设 Redis 服务器与客户端分处在异地，虽然基于内存的 Redis  数据库有着超高的性能，但是底层的网络通信却占用了一次数据请求的大量时间，因为每次数据交互都需要先建立连接，假设一次数据交互总共用时  30ms，超高性能的 Redis 数据库处理数据所花的时间可能不到 1ms，也即是说前期的连接占用了  29ms，连接池则可以实现在客户端建立多个连接并且不释放，当需要使用连接的时候通过一定的算法获取已经建立的连接，使用完了以后则还给连接池，这就免去了数据库连接所占用的时间。

#### redis持久化操作

<http://blog.itpub.net/28939273/viewspace-2653635/>

**Redis** 持久化 提供了多种不同级别的持久化方式:一种是**RDB(Redis DataBase)**,另一种是**AOF(Append Only File)**.
**RDB** 持久化可以在指定的时间间隔内生成数据集的时间点快照（point-in-time snapshot）。
**AOF** 持久化记录服务器执行的所有写操作命令，并在服务器启动时，通过重新执行这些命令来还原数据集redis重启后数据还在，是因为有持久化策略。

**redis默认**开启rdb持久化策略，会产一个dump.rdb文件，重启时会从该文件导入数据。如果是配置了AOF持久化策略，也会产一个相应的文件，当两种持久化同时开启时，redis重启时会优先从AOF文件导入数据。

查看`dump.rdb`可以通过`sudo find / -name dump.rdb`查看

**优缺点：**

**RDB** 可以最大化 Redis 的性能：父进程在保存 RDB 文件时唯一要做的就是 fork 出一个子进程，然后这个子进程就会处理接下来的所有保存工作，父进程无须执行任何磁盘 I/O 操作。RDB 在恢复大数据集时的速度比 AOF 的恢复速度要快。

**RDB** 文件需要保存整个数据集的状态， 所以它并不是一个轻松的操作。 因此你可能会至少 5 分钟才保存一次 RDB 文件。 在这种情况下， 一旦发生故障停机， 你就可能会丢失好几分钟的数据。

**AOF **的默认策略为每秒钟 fsync 一次，在这种配置下，Redis 仍然可以保持良好的性能，并且就算发生故障停机，也最多只会丢失一秒钟的数据（ fsync 会在后台线程执行，所以主线程可以继续努力地处理命令请求）。

**AOF **文件的体积通常要大于 RDB 文件的体积。根据所使用的 fsync 策略，AOF 的速度可能会慢于 RDB 。

**开启RDB持久化方式**

开启RDB持久化方式很简单，客户端可以通过向Redis服务器发送save或bgsave命令让服务器生成rdb文件，或者通过服务器配置文件指定触发RDB条件。

1. **save配置**

   **手工触发**

   save：会造成Redis阻塞，所有后续到达的命令要等待save完成以后才能执行

   ```shell
   127.0.0.1:6379> save
   OK
   ```

   另一种是 bgsave 命令：Redis进程执行fork操作创建子进程，RDB持久化过程由子 进程负责，完成后自动结束。阻塞只发生在fork阶段，一般时间很短

   ```shell
   127.0.0.1:6379> bgsave
   Background saving started
   ```

   **服务器配置自动触发**

   save 配置是一个非常重要的配置，它配置了 redis 服务器在什么情况下自动触发 bgsave 异步 RDB 备份文件生成。打开`/etc/redis/redis.conf`

   ```conf
   save <seconds> <changes>
   ```

   可以配置多条save指令，让Redis执行多级的快照保存策略。

   Redis默认开启RDB快照，默认的RDB策略如下：

   ```conf
   save 900 1
   save 300 10
   save 60 10000
   ```

   当 redis 数据库在\<seconds>秒内，数据库中的 keys 发生了\<changes>次变化，那么就会触发bgsave命令的调用。

   之后在启动服务器时加载配置文件。

   ```conf
   # 启动服务器加载配置文件
   redis-server redis.conf
   ```

**开启AOF持久化方式**

1. **服务器配置**

   Redis默认不开启AOF持久化方式，我们可以在配置文件中开启并进行更加详细的配置，如下面的`redis.conf`文件：

   ```conf
   # 开启aof机制
   appendonly yes
   
   # aof文件名
   appendfilename "appendonly.aof"
   
   # 写入策略,always表示每个写操作都保存到aof文件中,也可以是everysec或no
   appendfsync always
   
   # 默认不重写aof文件
   no-appendfsync-on-rewrite no
   
   # 保存目录
   dir ~/redis/
   ```

   在上面的配置文件中，我们可以通过appendfsync选项指定写入策略，有三个选项

   ```conf
   appendfsync always  # 客户端的每一个写操作都保存到aof文件当，这种策略很安全，但是每个写请注都有IO操作，所以也很慢
   appendfsync everysec  # appendfsync的默认写入策略，每秒写入一次aof文件，因此，最多可能会丢失1s的数据
   appendfsync no  # Redis服务器不负责写入aof，而是交由操作系统来处理什么时候写入aof文件。更快，但也是最不安全的选择，不推荐使用
   ```

2. **AOF文件重写**

   **手动重写**

   ```shell
   127.0.0.1:6379> bgrewriteaof
   ```

   **服务器自动配置**

   打开`redis.conf`

   ```shell
   # 默认不重写aof文件
   no-appendfsync-on-rewrite no
   
   # 两个配置项的意思是，在aof文件体量超过64mb，且比上次重写后的体量增加了100%时自动触发重写
   auto-aof-rewrite-percentage 100
   auto-aof-rewrite-min-size 64mb
   ```

   

### 异步任务：

#### 创建Flask服务：

这里的flask项目名称为`FlaskModel`，目录结构如下：

注：通过`sudo apt-get -y  install tree`安装`tree`，再在项目目录下输入`tree -I node_modules > tree.txt`得到如下项目结构树

```txt
.
├── app
│   ├── api
│   │   ├── celery_worker.py
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── modelInferenceAPI.py
│   │   ├── redisdbOperationAPI.py
│   │   └── test.py
│   ├── database
│   │   ├── __init__.py
│   │   ├── redis_db.py
│   ├── extensions.py
│   ├── __init__.py
│   └── utils
│       ├── dicom_process.py
│       ├── __init__.py
│       ├── postprocess.py
│       └── tf_gRPC_dicom_batch_app.py
├── app.log
├── config
│   ├── config.py
│   ├── logger.py
│   ├── supervisords_celery.ini
│   └── supervisords_gunicorn.ini
├── gun.py
├── instance
├── logs
│   └── celeryworker.log
├── manage.py
├── requirements.txt
└── tree.txt

13 directories, 43 files

```

### 利用Gunicorn部署Flask服务：

项目中`gun.py`中是gunicorn配置信息，`manage.py`是app管理脚本，单独使用`gunicorn`的命令是

```shell
gunicorn -c gun.py manage:app 
```

这时候会显示

```shell
(qsj) qiushenjie@ubuntu:~/qiushenjie/FlaskModel$ gunicorn -c gun.py manage:app 
[2020-10-22 20:03:00 +0800] [29039] [INFO] Starting gunicorn 19.9.0
[2020-10-22 20:03:00 +0800] [29039] [INFO] Listening at: http://127.0.0.1:5000 (29039)
[2020-10-22 20:03:00 +0800] [29039] [INFO] Using worker: gunicorn.workers.ggevent.GeventWorker
[2020-10-22 20:03:00 +0800] [29042] [INFO] Booting worker with pid: 29042
[2020-10-22 20:03:00 +0800] [29044] [INFO] Booting worker with pid: 29044
[2020-10-22 20:03:00 +0800] [29045] [INFO] Booting worker with pid: 29045
[2020-10-22 20:03:00 +0800] [29047] [INFO] Booting worker with pid: 29047
```

说明运行成功

### 利用Supervisor部署gunicorn

#### supervisor介绍

Supervisor是用Python开发的一套通用的进程管理程序，能将一个普通的命令行进程变为后台daemon，并监控进程状态，异常退出时能自动重启。它是通过fork/exec的方式把这些被管理的进程当作supervisor的子进程来启动，这样只要在supervisor的配置文件中，把要管理的进程的可执行文件的路径写进去即可。也实现当子进程挂掉的时候，父进程可以准确获取子进程挂掉的信息的，可以选择是否自己启动和报警。

生成配置文件，

```shell
echo_supervisord_conf > supervisords.conf
sudo mv supervisords.conf /etc/supervisords.conf
```

下面是常用的配置方法：

```conf
[unix_http_server]
file=/tmp/supervisor.sock   ;UNIX socket 文件，supervisorctl会使用其与supervisord通信
;chmod=0700                 ;socket文件的mode，默认是0700
;chown=nobody:nogroup       ;socket文件的owner，格式：uid:gid
  
;[inet_http_server]         ;HTTP服务器，提供web管理界面
;port=127.0.0.1:9001        ;Web管理后台运行的IP和端口，如果开放到公网，需要注意安全性
;username=user              ;登录管理后台的用户名
;password=123               ;登录管理后台的密码
  
[supervisord]
logfile=/tmp/supervisord.log ;日志文件，默认是 $CWD/supervisord.log
logfile_maxbytes=50MB        ;日志文件大小，超出会rotate，默认 50MB。如果设成0，表示不限制大小
logfile_backups=10           ;日志文件保留备份数量默认10，设为0表示不备份
loglevel=info                ;日志级别，默认info，其它: debug,warn,trace
pidfile=/tmp/supervisord.pid ;pid 文件
nodaemon=false               ;是否在前台启动，默认是false，即以 daemon 的方式启动
minfds=1024                  ;可以打开的文件描述符的最小值，默认 1024
minprocs=200                 ;可以打开的进程数的最小值，默认 200
  
[supervisorctl]
serverurl=unix:///tmp/supervisor.sock ;通过UNIX socket连接supervisord，路径与unix_http_server部分的file一致
;serverurl=http://127.0.0.1:9001 ; 通过HTTP的方式连接supervisord
  
; [program:xx]是被管理的进程配置参数，xx是进程的名称
[program:xx]
command=/opt/apache-tomcat-8.0.35/bin/catalina.sh run  ; 程序启动命令
autostart=true       ; 在supervisord启动的时候也自动启动
startsecs=10         ; 启动10秒后没有异常退出，就表示进程正常启动了，默认为1秒
autorestart=true     ; 程序退出后自动重启,可选值：[unexpected,true,false]，默认为unexpected，表示进程意外杀死后才重启
startretries=3       ; 启动失败自动重试次数，默认是3
user=tomcat          ; 用哪个用户启动进程，默认是root
priority=999         ; 进程启动优先级，默认999，值小的优先启动
redirect_stderr=true ; 把stderr重定向到stdout，默认false
stdout_logfile_maxbytes=20MB  ; stdout 日志文件大小，默认50MB
stdout_logfile_backups = 20   ; stdout 日志文件备份数，默认是10
; stdout 日志文件，需要注意当指定目录不存在时无法正常启动，所以需要手动创建目录（supervisord 会自动创建日志文件）
stdout_logfile=/opt/apache-tomcat-8.0.35/logs/catalina.out
stopasgroup=false     ;默认为false,进程被杀死时，是否向这个进程组发送stop信号，包括子进程
killasgroup=false     ;默认为false，向进程组发送kill信号，包括子进程
  
;包含其它配置文件
;[include]
;files = relative/directory/*.ini    ;可以指定一个或多个以.ini结束的配置文件
```

**本项目主要配置gunicorn和Celery，如下：**

在supervisor.conf中配置gunicorn(**这种方式不太推荐，详情见下文**)

```conf
[program:gunicorn]                                                           # gunicorn为进程的名字
user=qiushenjie	                                                             # 操作的用户
directory=/home/ubuntu/qiushenjie/FlaskModel                              # 项目目录，
command=/home/ubuntu/anaconda3/envs/qsj/bin/gunicorn -c gun.py manage:app    # 启动flask服务的命令，gunicorn命令路径通过whereis gunicorn查看，不然在supervisorctl start gunicorn时会报错
startsecs=5                                                                  # 启动5秒后没有异常退出，视作正常启动
autostart=true                                                               # 在 supervisord 启动时自动启动
autorestart=true                                                             # 程序异常退出后重启
redirect_stderr=true                                                         # 将错误信息重定向至stdout日志
stdout_logfile=/home/ubuntu/qiushenjie/FlaskModel/logs/gunicorn.pid    # 进程日志
```

**配置管理进程**

进程管理配置参数，不建议全都写在`supervisords.conf`文件中，建议每个进程写一个配置文件，并放在`include`配置块中`files`指定的目录下，通过`include`包含进 supervisords.conf 文件中。

将gunicorn的supervisor配置参数写在`/home/ubuntu/qiushenjie/FlaskModel/config/supervisords_gunicorn.ini`，如下：

```ini
[program:gunicorn]                                                           # gunicorn为进程的名字
user=qiushenjie	                                                             # 操作的用户
directory=/home/ubuntu/qiushenjie/FlaskModel                              # 项目目录，
command=/home/ubuntu/anaconda3/envs/qsj/bin/gunicorn -c gun.py manage:app    # 启动flask服务的命令，gunicorn命令路径通过whereis gunicorn查看，不然在supervisorctl start gunicorn时会报错
startsecs=5                                                                  # 启动5秒后没有异常退出，视作正常启动
autostart=true                                                               # 在 supervisord 启动时自动启动
autorestart=true                                                             # 程序异常退出后重启
redirect_stderr=true                                                         # 将错误信息重定向至stdout日志
stdout_logfile=/home/ubuntu/qiushenjie/FlaskModel/logs/gunicorn.pid    # 进程日志
```

修改配置文件 supervisords.conf：

```conf
[include]
;files = relative/directory/*.ini
files = /home/ubuntu/qiushenjie/FlaskModel/config/*.ini
```

**加载配置文件**

```shell
supervisord -c /etc/supervisords.conf
```

启动gunicorn

```shell
supervisorctl start gunicorn  # gunicorn即supervisor.conf中的[program:gunicorn]名称
```

supervisor的常用命令

```shell
#开启命令
supervisorctl status                # 获取所有进程状态
supervisorctl stop gunicorn         # 停止进程 
supervisorctl start gunicorn        # 启动进程 
supervisorctl restart gunicorn      # 重启进程，不会重新加载配置文件 
supervisorctl reread                # 重新加载配置文件，不会新增和删除进程 
supervisorctl update                # 加载配置文件，会删除和新增进程，并重启受影响的程序 
supervisorctl shutdown              # 停止supervisord  
supervisorctl start stop restart all# 停止全部进程
#关闭命令
supervisorctl stop all              # 先关闭supervisor服务
kill -9 pid                         # 之后再关闭supervisord服务
```

这时我们继续访问接口，如果可以正常访问，那就证明没有问题。

上面的开启方式可能会报下面DEBUG的错误，因此最好每次启动`supervisor`都运行

```shell
supervisord -c /etc/supervisords.conf
supervisorctl
```

输入账号密码

终端显示

```shell
gunicorn                         RUNNING   pid 16329, uptime 0:00:20
supervisor>
```



关闭流程为

```shell
supervisor>stop all
supervisor>shutdown
supervisor>exit
```

### 利用celery部署异步任务

创建`celery_worker.py`

修改`api`接口文件

重启flask服务：

```shell
supervisorctl restart gunicorn   # 这个过程可能会报错，具体报错即解决方法查看下面的DEBUG部分
```

启动celery服务

首先确保`celery_worker.py`里实例化Celery的任务与项目相同，即`Celery("FlaskModel", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)`，因为`celery_worker.py`的路径在`app/api下，因此在终端启动Celery的命令为

```shell
celery -A app.api worker --loglevel=info
```

终端会显示

```shell
(qsj) qiushenjie@ubuntu:~/qiushenjie/FlaskModel$ celery -A app.api worker --loglevel=info
 
 -------------- celery@ubuntu v5.0.1 (singularity)
--- ***** ----- 
-- ******* ---- Linux-4.15.0-120-generic-x86_64-with-debian-stretch-sid 2020-10-23 17:35:54
- *** --- * --- 
- ** ---------- [config]
- ** ---------- .> app:         FlaskModel:0x7f56b1193cc0
- ** ---------- .> transport:   redis://127.0.0.1:6379/0
- ** ---------- .> results:     redis://127.0.0.1:6379/0
- *** --- * --- .> concurrency: 16 (prefork)
-- ******* ---- .> task events: OFF (enable -E to monitor tasks in this worker)
--- ***** ----- 
 -------------- [queues]
                .> celery           exchange=celery(direct) key=celery
                

[tasks]
  . app.views.celery_worker.inference

[2020-10-23 17:35:54,878: INFO/MainProcess] Connected to redis://127.0.0.1:6379/0
[2020-10-23 17:35:54,885: INFO/MainProcess] mingle: searching for neighbors
[2020-10-23 17:35:55,901: WARNING/MainProcess] /home/ubuntu/anaconda3/envs/qsj/lib/python3.6/site-packages/celery/app/control.py:50: DuplicateNodenameWarning: Received multiple replies from node name: celery@ubuntu.
Please make sure you give each node a unique nodename using        # 出现这个DuplicateNodenameWarning可能会导致之后报错，所以最好在开启celery之前先关闭其他celery进程
the celery worker `-n` option.
  pluralize(len(dupes), 'name'), ', '.join(sorted(dupes)),

[2020-10-23 17:35:55,902: INFO/MainProcess] mingle: all alone
[2020-10-23 17:35:55,919: INFO/MainProcess] celery@ubuntu ready.
```

但如果我们在`app/__init__.py`中`from app.api.celery_worker import CLASSMODEL`即导入这个celery实例，这时命令行可以更简洁一点，如下：

```shell
celery -A app.CLASSMODEL worker --loglevel=info
```

同样可以正常使用。

注：如果想关闭所有Celery进程，输入下面的命令

```shell
ps auxww|grep "celery"|grep -v grep|awk '{print $2}'|xargs kill -9
```

这里`celery_worker.py`中的任务函数如果又另外需要引用外部函数

比如任务函数如下

```shell
import request_server  # request_server()及为外部函数
celery = Celery("FlaskModel",
                    broker=CELERY_BROKER_URL,
                    backend=CELERY_RESULT_BACKEND,
                    CELERY_TASK_SERIALIZER='json',
                    )

@celery.task  # 这里写了一个异步方法，等待被调用
def inference(image_path):
    res = request_server(image_path)
    return res

def get_result(task_id):  # 通过任务id可以获取该任务的结果
    result = celery.AsyncResult(task_id)
    return result.result
```

在运行时大概率会报错

```shell
RuntimeError: Working outside of application context.

This typically means that you attempted to use functionality that needed
to interface with the current application object in some way. To solve
this, set up an application context with app.app_context().  See the
documentation for more information.
```

这是因为当你在一个没有上下文环境的模块中，直接引入request和current_app并且直接使用它时，会报错，所以需要在脚本中获取应用上下文环境。

解决方案就是，把需要引用 `Flask app `的地方（如` app.config`），放到 Flask 的`application context`里执行。如在本项目的`/manager.py`中创建app实例后往celery推入flask信息，使得celery能使用flask上下文：

```shell
app = create_app('ProductionConfig')
app.app_context().push()

manager = Manager(app)
```

在实际应用中，也可以写了个装饰器来实现这个目的，重写`celery_worker.py`如下

```shell
import request_server  # request_server()及为外部函数
celery = Celery("FlaskModel",
                    broker=CELERY_BROKER_URL,
                    backend=CELERY_RESULT_BACKEND,
                    CELERY_TASK_SERIALIZER='json',
                    )

def with_app_context(task):
    memo = {'app': None}

    @functools.wraps(task)
    def _wrapper(*args, **kwargs):
        if not memo['app']:
            from app import create_app

            app = create_app()
            memo['app'] = app
        else:
            app = memo['app']

        # 把 task 放到 application context 环境中运行
        with app.app_context():
            return task(*args, **kwargs)

    return _wrapper

@celery.task  # 这里写了一个异步方法，等待被调用
@with_app_context
def inference(image_path):
    res = request_server(image_path)
    return res

def get_result(task_id):  # 通过任务id可以获取该任务的结果
    result = celery.AsyncResult(task_id)
    return result.result
```

gunicorn和celery开启后，测试接口：

```shell
(qsj) qiushenjie@ubuntu:~/qiushenjie/FlaskModel$ curl http://127.0.0.1:5000/inference/3/0/100

69d5a3f3-9d3e-4db1-98d4-41118a11279a(qsj) qiushenjie@ubuntu:~/qiushenjie/FlaskModel$ # 得到任务id：69d5a3f3-9d3e-4db1-98d4-41118a11279a

69d5a3f3-9d3e-4db1-98d4-41118a11279a(qsj) qiushenjie@ubuntu:~/qiushenjie/FlaskModel$ curl http://127.0.0.1:5000/get_result/69d5a3f3-9d3e-4db1-98d4-41118a11279a  # 通过任务id查看任务结果
```

说明测试成功

接下来在supervisor中部署celery，在/etc/supervisord.conf中添加如下内容：

```shell
[program:celeryworker]                          # celeryworker是进程的名字，随意起
command=celery -A app.CLASSMODEL worker --loglevel=info
directory=/home/ubuntu/qiushenjie/FlaskModel            # 项目路径，
user=qiushenjie
numprocs=1
# 设置log的路径
stdout_logfile=/home/ubuntu/qiushenjie/FlaskModel/logs/celeryworker.log
stderr_logfile=/home/ubuntu/qiushenjie/FlaskModel/logs/celeryworker.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs = 6000
priority=15
```

更新supervisor配置

```shell
supervisorctl update
```

显示

```shell
celeryworker: added process group
```

则说明更新成功

也有可能报错

```shell
error: <class 'ConnectionRefusedError'>, [Errno 111] Connection refused: file: /home/ubuntu/anaconda3/envs/qsj/lib/python3.6/socket.py line: 713
```

解决方法：

待定



#### 将数据存入redis数据库

首先写一个Redis数据库操作类

```python
from config import config  # config.py中包含了redis的一些信息，比如host, port, 数据库名称
import redis

class Redis(object):
    """
    redis数据库操作
    """

    @staticmethod
    def _get_r():
        # 当Redis类作为一个appAPI使用时，例如在redisdbOperationAPI.py中调用，会被注册进蓝本，因此可直接从current_app中获取配置信息
		# from flask import current_app
        # host = current_app.config['REDIS_HOST']
        # port=current_app.config['REDIS_PORT']
        # db=current_app.config['REDIS_DB']
        
        # 因为Redis类会在modelInferenceAPI直接使用，因此暂时不从current_app中获取配置信息，而是直接从config中获取
        host = config.redis_map['REDIS_HOST'] 
        port=config.redis_map['REDIS_PORT']
        db=config.redis_map['REDIS_DB']
        r = redis.StrictRedis(host, port, db)
        return r

    @classmethod
    def write(self, key, value, expire=None):
        """
        写入键值对
        """
        # 判断是否有过期时间，没有就设置默认值
        if expire:
            expire_in_seconds = expire
        else:
            # expire_in_seconds = current_app.config['REDIS_EXPIRE']
            expire_in_seconds = expire
        r = self._get_r()
        r.set(key, value, ex=expire_in_seconds)

    @classmethod
    def read(self, key):
        """
        读取键值对内容
        """
        r = self._get_r()
        value = r.get(key)
        return value.decode('utf-8') if value else value
```

在相应的API中实例化Redis类并进行增删查改操作，比如在`celery_worker.py`的`inference()`中：

```python
from app.database.redis_db import Redis

Redis.write(key, value)
```

即可在对应的redis数据库中写入键值对



### 配置nginx反向代理

安装好了nginx，接下来直接配置即可

```shell
cd /etc/nginx/sites-enabled/
rm default
vim app

server {
    listen 80;
    server_name _;                           # 有域名可以配置在这里
    access_log  /var/log/nginx/access.log;    
    error_log  /var/log/nginx/error.log;
    location / {
        proxy_pass         http://127.0.0.1:5000/;     # 转发服务的地址
        proxy_redirect     off;
 
        proxy_set_header    Host                 $host;
        proxy_set_header    X-Real-IP            $remote_addr;
        proxy_set_header    X-Forwarded-For      $proxy_add_x_forwarded_for;
        proxy_set_header    X-Forwarded-Proto    $scheme;
    }
}
```

测试配置文件是否正确

```shell
nginx -t
```

没有报错则重启nginx

```shell
nginx -s reload 或者 service nginx restart
```

再次测试接口是否可用，如果没有报错，那么整个部署步骤到此为止。



### 最后

整个web服务的开启流程是

```shell
supervisord -c /etc/supervisords.conf
supervisorctl
```

显示

```shell
Server requires authentication
Username:    # 输入supervisords.conf中的用户名
Password:    # 输入supervisords.conf中的密码
```

显示

```shell
celeryworker                     RUNNING   pid 24855, uptime 0:00:17
gunicorn                         RUNNING   pid 24856, uptime 0:00:17
supervisor>        # 这里可以进行进程stop,start,restart等操作
```

最后，运行客户端，例如

```shell
curl http://127.0.0.1:5000/inference/3/0/100
```

得到一个`task_id`比如`fb049cc4-f649-4c6e-843d-9b52f4f909b1`，通过这个任务id获取结果

```shell
curl http://127.0.0.1:5000/get_result/fb049cc4-f649-4c6e-843d-9b52f4f909b1
```









### Debug

#### 1.supervisord报错

运行

```shell
supervisord -c /etc/supervisords.conf
```

出现错误

```shell
Starting supervisor: Error: Another program is already listening on a port that one of our HTTP servers is configured to use.  Shut this program down first before starting supervisord.
For help, use /usr/bin/supervisord -h
```

解决办法

Terminal上输入

```shell
ps -ef | grep supervisord
```

获取所有supervisord正在运行的pid

```shell
qiushen+  1900  2043  0 12:49 ?        00:00:01 /home/ubuntu/anaconda3/envs/qsj/bin/python /home/ubuntu/anaconda3/envs/qsj/bin/supervisord -c /etc/supervisords.conf
qiushen+  5733 21484  0 15:12 pts/2    00:00:00 grep --color=auto supervisord
```

杀进程`1900`即可

之后在重新执行

```shell
supervisord -c /etc/supervisords.conf
```

#### 2.supervisorctl start gunicorn报错

运行

```shell
supervisorctl start gunicorn
```

出现

```shell
http://localhost:9001 refused connection
```

解决方法

打开`/etc/supervisords.conf`

```shell
sudo gedit supervisords.conf
```

将这四行的开头的`;`去掉即可

```txt
;[inet_http_server]         ; inet (TCP) server disabled by default
;port=127.0.0.1:9001        ; ip_address:port specifier, *:port for all iface
;username=user              ; default is no username (open server)
;password=123               ; default is no password (open server)
```

#### 3.supervisord -c /etc/supervisords.conf报错

出现

```shell
Unlinking stale socket /tmp/supervisor.sock
```

解决方法

输入

```shell
unlink /tmp/supervisor.sock
```

#### 4.supervisorctl start gunicorn或者supervisorctl shutdown报错

出现

```shell
Server requires authentication
error: <class 'xmlrpc.client.ProtocolError'>, <ProtocolError for 127.0.0.1/RPC2: 401 Unauthorized>: file: /data/python_envs/es-service/lib/python3.7/site-packages/supervisor/xmlrpc.py line: 545
```

这是因为开启了权限验证导致，可以通过执行supervisorctl 回车输入用户名+密码 进入之后进行shutdown操作，账号密码在`/etc/supervisor/supervisords.conf`中的`[inet_http_server]`中查看

流程如下

```shell
(qsj) qiushenjie@ubuntu:~/qiushenjie/FlaskModel$ supervisorctl
Server requires authentication
Username:user
Password:123

```

输入账号密码后显示

```shell
gunicorn                         RUNNING   pid 16329, uptime 0:00:20  # 有一个gunicorn在运行了
supervisor> restart gunicorn       #这里输入supervisor的操作
```

会出现

```shell
gunicorn: stopped
gunicorn: started
supervisor>
```

运行成功

supervisor的客户端部分命令

```txt
supervisorctl status 查看进程运行状态
supervisorctl start 进程名 启动进程
supervisorctl stop 进程名 关闭进程
supervisorctl restart 进程名 重启进程
supervisorctl update 重新载入配置文件
supervisorctl shutdown 关闭supervisord
supervisorctl clear 进程名 清空进程日志
supervisorctl 进入到交互模式下。使用help查看所有命令。
start stop restart + all 表示启动，关闭，重启所有进程。
```

#### 5.开启celery出现`DuplicateNodenameWarning`

出现

```shell
DuplicateNodenameWarning: Received multiple replies from node name: celery@ubuntu.
Please make sure you give each node a unique nodename using
the celery worker `-n` option.
  pluralize(len(dupes), 'name'), ', '.join(sorted(dupes)),
```

解决方法

可能是有其他celey进程未关闭

终端输入

```shell
ps auxww|grep "celery worker"|grep -v grep|awk '{print $2}'|xargs kill -9
```

关闭所有celery进程
