FROM node:20-slim

# HF Spaces 必须监听 7860
ENV PORT=7860

# 数据统一落在 /app/data（会软链到 HF 的 /data 持久盘）
ENV DATA_DIR=/app/data
ENV HOME=/app/data

WORKDIR /app

# 先装依赖（便于 Docker 缓存）
COPY package*.json ./
RUN npm install --omit=dev

# 安装 OpenClaw CLI + QQ 插件（全局）
RUN npm install -g openclaw@latest @sliverp/qqbot@latest @creatoraris/openclaw-qq@latest

# 拷贝代码
COPY . .

# HF Spaces 持久化盘挂载在 /data，这里把 /app/data 指到 /data
RUN mkdir -p /data \
  && (test -e /app/data || ln -s /data /app/data)

EXPOSE 7860

CMD ["node", "index.js"]
