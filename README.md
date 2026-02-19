# AI X News Hub

一个自动聚合 X（通过公开 RSS 镜像）上 AI/科技内容的轻量站点。

## 本地运行

```bash
cd ai-x-news-hub
python3 fetch_news.py
python3 -m http.server 8787
```

访问：`http://127.0.0.1:8787`

## 每日自动更新

通过 crontab 每天定时执行：

```bash
python3 /Users/yeadon_1/.openclaw/workspace/ai-x-news-hub/fetch_news.py
```

## 公网访问（内网穿透）

使用 localtunnel：

```bash
npx localtunnel --port 8787 --subdomain yeadon-ai-news
```

如果子域被占用，去掉 `--subdomain` 自动分配。
