# 宝塔面板 Docker 部署教程

## 前提

- 服务器已安装[宝塔面板](https://www.bt.cn/)
- 宝塔已安装 **Docker** 和 **Docker Compose** 插件
- 已安装[果](https://www.bt.cn/plugin/details?id=9168)（或直接在终端操作）

---

## 方式一：宝塔终端（最快，推荐）

### Step 1：上传项目文件

在宝塔 **文件** 页面，进入 `/www/wwwroot/`，新建文件夹 `music-generator`。

有两种方式上传：

**方式 A：Git 克隆（推荐）**
```
进入宝塔面板 → 终端
cd /www/wwwroot/
git clone https://github.com/Ancoren/music-generator.git
cd music-generator
```

**方式 B：上传压缩包**
- 在本机解压 `music-generator` 压缩包
- 宝塔文件管理器上传整个文件夹到 `/www/wwwroot/music-generator`

---

### Step 2：配置 API Key

在宝塔文件管理器，进入 `/www/wwwroot/music-generator/`，新建文件 `.env`：

```
MINIMAX_API_KEY=你的API密钥
API_BASE_URL=https://api.minimax.chat
```

---

### Step 3：修改 docker-compose.yml（可选，绑定端口）

宝塔的 Docker 容器管理可以直接映射端口。如果想改访问端口，修改 `docker-compose.yml` 中的端口：

```yaml
  nginx:
    ports:
      - "8888:80"    # 把 8888 改成你想要的端口
```

---

### Step 4：一键启动

在宝塔 **终端** 执行：

```bash
cd /www/wwwroot/music-generator
docker-compose up -d --build
```

查看日志确认启动成功：

```bash
docker-compose logs -f backend
```

---

### Step 5：开放端口（防火墙）

宝塔 **安全** → **防火墙** → 添加入站规则：
- 端口：`8888`（或你改的端口）
- 策略：允许
- 备注：AI音乐生成器

同时在服务器控制台（厂商控制台）开放对应端口。

---

### Step 6：访问

浏览器打开：`http://你的服务器IP:8888`

---

## 方式二：宝塔 Docker 管理器（图形化）

如果你的宝塔装了 **Docker Compose** 插件，可以完全图形化操作：

### Step 1：上传项目

同方式一 Step 1。

### Step 2：在 Docker Compose 插件中操作

1. 打开宝塔 **Docker** → **Docker Compose**
2. 点击 **创建Compose**
3. **项目目录** 选择：`/www/wwwroot/music-generator`
4. **编排内容** 复制 `docker-compose.yml` 里的内容进去
5. **环境变量** 添加：
   - `MINIMAX_API_KEY` = `你的API密钥`
   - `API_BASE_URL` = `https://api.minimax.chat`
6. 点击 **创建** → 等待镜像拉取和构建完成

### Step 3：端口映射

创建时指定端口映射，或创建后在容器列表找到 `music-generator-nginx-1`，点击 **端口映射** 查看。

### Step 4：访问

同方式一 Step 6。

---

## 宝塔坑点排查

| 问题 | 解决 |
|------|------|
| 502 Bad Gateway | 容器未启动 → 检查 backend 是否运行：`docker ps` |
| 连接被拒绝 | 防火墙/安全组未开放端口 |
| 容器启动后立即退出 | `.env` 未创建或 `MINIMAX_API_KEY` 为空 |
| 镜像拉取失败 | 宝塔所在服务器无法访问 Docker Hub → 换国内镜像源 |
| 构建失败 | SSH 进服务器手动 `docker-compose build` 看错误信息 |

---

## 更新项目

```bash
cd /www/wwwroot/music-generator
git pull origin main
docker-compose up -d --build
```
