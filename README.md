##部署安装步骤：

###一、备份服务端管理节点部署安装

####1. 获取安装包并解压

我们可以从如下地址获取所有需要的安装包

```bash
wget http://xxxx
```

然后解压

```bash
tar zxf xxxxxxx.tar.gz
```

####2. 环境初始化


#####2.1. MySql数据库安装与配置

管理节点需要安装MySql数据库存来储备份管理数据。你需要安装MySql服务，并配置数据库用户，并赋予用户创建数据库权限。
安装MySql数据库方法请参照MySql官方文档，这里不做详述。
创建用户并配置用户权限命令如下：

```bash

```

#####2.2. python环境初始化和相关依赖安装

我们约定使用python版本为2.7，如果当前系统python版本小于2.7，我们将为你安装python-2.7.8。这不会影响你已有python应用的正常使用，且不会替换原来的python版本。
执行命令如下：

```bash

```

#####2.3 管理节点服务配置和安装

在/etc目录下新建目录fbmp

```bash
mkdir /etc/fbmp
```

2) 



2.4. Glusterfs Fuse Client安装
安装包  目录下分别含有Centos6.x和Centos7.x版本的客户端运行库同时。我们也将RPM二进制包放在目录下，方便使用YUM进行安装，如果你的服务器上使用YUM安装后运行命令失败，建议你用使用第二种方法安装。
2.4.1 YUM安装

2.4.2 安装客户端链接库

2.4 
		





二、备份客户端备份节点部署安装









### 自动化安装脚本setup使用说明 ###

- **config配置**

在根目录下的config文件用来记录client和server的地址信息，在启动client的时候会根据该信息启动client服务，如：

```txt
glusterfs_ip = 10.10.10.10:8080
web_ip = 10.10.10.11.8080
```
- **setup使用**

首先setup需要有可执行权限，执行如下命令可以查看帮助信息

    ./setup
    
提示信息如下，请按照说明进行执行命令

    Usage:
      ./setup <command> <options>
    Commands:
      initial            Runtime environment initialization.               
      start              Startup Programs.                                 
      stop               Stop Programs.                                    
    Initial Options:
      -p, --python       Only initialized to the Python runtime environment.
      -c, --client       Only initialized to the client runtime environment.
      -s, --server       Only initialized to the web server runtime environment.
      -a, --all          Initialized to the web server and client runtime environment.
    Start Options:
      -c, --client       Startup client program on the host.               
      -s, --server       Startup web server program on the host.           
    Stop Options:
      -c, --client       Stop client program on the host.                  
      -s, --server       Stop web server program on the host.

>**注意**： 在只运行客户端或者服务端程序时，需要先初始化python环境，然后初始化client或者web server环境；

>setup并不包含前端页面资源打包，发布的web前端产品需要参考本文后面webpack打包说明



----------
### 手动安装 ###

#### 安装python库 ####

这里默认python版本为2.7，如果服务器python版本小于2.7，请先安装python2.7，在后面补充章节有具体介绍如何使用

在项目目录执行命令

    pip install --no-index -f requirePackage -r requirements.txt

本地单独安装python2.7下，库安装命令
	
	/usr/local/bin/python2.7 -m pip install --no-index -f requirePackage -r requirements.txt
	

如果服务器上没有pip，或者本地单独安装了python2.7版本，先安装pip。打开requirePackage
    
    cd requirePackage
    
解压pip-9.0.1.tar.gz

    tar xzf pip-9.0.1.tar.gz
    
打开解压后的目录pip-9.0.1，进行安装

    cd pip-9.0.1
    python setup.py install

本地单独安装python2.7情况下使用如下命令

	/usr/local/bin/python2.7 setup.py install

**本地安装python2.7环境**

本节作为补充章节，为了解决目前生产环境存在少量python2.6版本的服务器上部署备份软件报版本无法兼容问题。

首先需要执行如下命令安装zlib，如果已经安装过，此步可以跳过

    yum install zlib
    yum install zlib-devel

在本目录可以看到Python-2.7.8.tgz安装包，解压
	
	tar xf Python-2.7.8.tgz

进入目录

	cd Python-2.7.8

配置python2.7安装目录，注意不要与原有python目录冲突。这里我们指定安装到/usr/local目录

	./configure --prefix=/usr/local

执行安装，这一过程大约需要2-3分钟

	make && make install

验证，执行命令

	/usr/local/bin/python2.7

> **注意**： 在此方法下，所有使用python2.7版本时都应使用上述全路径命令

安装setuptools，进入requirePackage

    cd requirePackage
    
解压setuptools-23.1.0.tar.gz

    tar xzf setuptools-23.1.0.tar.gz

打开目录setuptools-23.1.0，执行命令安装

    cd setuptools-23.1.0
    /usr/local/bin/python2.7 setup.py install

然后按照前面安装pip方法为python2.7安装pip

#### Nginx 配置参考#####

```text
server {
	listen      6060;
        server_name sf;

        return 301 https://$host$request_uri;
    }



server {
        listen  443 ssl default_server;
        server_name  sf;
        ssl_certificate           /home/cert.crt;
        ssl_certificate_key       /home/cert.key;

        ssl on;
        ssl_session_cache  builtin:1000  shared:SSL:10m;
        ssl_protocols  TLSv1 TLSv1.1 TLSv1.2;
        ssl_ciphers HIGH:!aNULL:!eNULL:!EXPORT:!CAMELLIA:!DES:!MD5:!PSK:!RC4;
        ssl_prefer_server_ciphers on;

	location / {
            proxy_pass_request_headers on;
            proxy_set_header     HTTP_AUTHORIZATION $http_authorization;
            proxy_set_header    Host $host;
            proxy_pass             http://backupserver;
        }

}

```

#### WEB Server ####

server配置文件：

```text
[global]
#访问端口，默认为80
server.socket_port: 9090		
server.socket_host: '0.0.0.0'

[database]
driver = 'mysql'
user = 'backup'
password = '123456'
host = '10.202.127.11'
database = 'test'

[Token]
iss = 'SFBACKUP'
exp = 3600

[/]
tools.sessions.on: True
tools.sessions.storage_class = cherrypy.lib.sessions.FileSession
#sessions目前没有实际使用，但需要web目录下游sessions文件夹
tools.sessions.storage_path = os.path.join(os.getcwd(), "sessions") 
tools.sessions.secure = True
tools.sessions.httponly = True
#允许跨域访问
tools.CORS.on = True		

[/dist]
tools.staticdir.on = True
#静态资源目录
tools.staticdir.root = os.path.join(os.getcwd(),"static")
tools.staticdir.dir = "dist"
#页面入口
tools.staticdir.index = "index.html"

[/backup]
request.dispatch = cherrypy.dispatch.MethodDispatcher()
tools.response_headers.on = True


[/favicon.ico]
tools.staticfile.on: True
tools.staticfile.filename: os.path.join(os.getcwd(), "static/sf.ico")
```

日志配置文件为logging.conf

**安装Vuejs依赖组件和webpack工具**

可以参考[文档](http://blog.huichen.info/2017/08/10/vuejs-demo/)

**拷贝静态资源**

拷贝web目录下index.html文件到static目录下

    cd web
    cp -f index.html ../static/

**Webpack打包**

进入web目录

    cd  server/web/

执行webpack打包命令

	webpack

**启动web server**

在server目录下执行命令

	/bin/python server.py

本地单独安装python2.7情况下使用如下命令

	/usr/local/bin/python2.7 server.py
	
#### Client ####

在安装客户端的服务器上执行命令,我们建议是这个目录，可以根据自己实际环境调整。
	
	mkdir -p /data/work/

将client目录下libgfapi-python-master.zip 拷贝到/data/work/ 中解压，然后执行
	
	python setup.py install

本地单独安装python2.7情况下使用如下命令

	/usr/local/bin/python2.7 setup.py install

更新动态库

	cp lib* /lib64/
	cd /lib64
	ln -s libgfapi.so.0.0.0 libgfapi.so.0
	ln -s libgfrpc.so.0.0.1 libgfrpc.so.0
	ln -s libgfxdr.so.0.0.1 libgfxdr.so.0
	ln -s libglusterfs.so.0.0.1 libglusterfs.so.0
	ln -s libgfchangelog.so.0.0.1 libgfchangelog.so.0

将start.py 放到/data/work目录下
	
以root 权限执行脚本

	python start.py start gluster-serverip webserverip:port

本地单独安装python2.7情况下使用如下命令

	/usr/local/bin/python2.7 start.py start gluster-serverip webserverip:port
	
如

	python start.py start 10.202.233.55 10.202.233.56：8080

> 其中，gluster-serverip 是指gluster集群的其中一个server 的ip，为了保证容错，不能所有的client都填同一个server的ip