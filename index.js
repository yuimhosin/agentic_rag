const express = require('express')
const fs = require('fs')
const path = require('path')
const { spawn } = require('child_process')

const app = express()
const port = Number(process.env.PORT || 7860)

// 从环境变量读取（不要硬编码）
const QQ_ID = process.env.QQ_ID || ''
const QQ_PASSWORD = process.env.QQ_PASSWORD || ''
const LLM_API_KEY = process.env.LLM_API_KEY || ''
const GATEWAY_TOKEN = process.env.GATEWAY_TOKEN || ''

// 数据目录固定到 /app/data（Dockerfile 会软链到 /data 持久盘）
const DATA_DIR = process.env.DATA_DIR || '/app/data'

function ensureDir(p) {
  fs.mkdirSync(p, { recursive: true })
}

function writeOpenClawConfig() {
  const openclawHome = path.join(DATA_DIR, '.openclaw')
  const cfgPath = path.join(openclawHome, 'openclaw.json')
  ensureDir(openclawHome)

  // 注意：openclaw.json 不支持 $ENV_VAR 写法，所以这里用启动时生成配置文件
  const cfg = {
    models: {
      providers: {
        deepseek: {
          baseUrl: 'https://api.deepseek.com/v1',
          apiKey: LLM_API_KEY,
          api: 'openai-completions',
          models: [
            { id: 'deepseek-chat', name: 'DeepSeek Chat' },
            { id: 'deepseek-reasoner', name: 'DeepSeek Reasoner' },
          ],
        },
      },
    },
    agents: {
      defaults: { model: { primary: 'deepseek/deepseek-chat' } },
    },
  }

  // 官方 qqbot：token 形如 AppID:AppSecret
  if (QQ_ID && QQ_PASSWORD) {
    cfg.channels = cfg.channels || {}
    cfg.channels.qqbot = {
      enabled: true,
      accounts: {
        default: { token: `${QQ_ID}:${QQ_PASSWORD}` },
      },
    }
  }

  // 普通账号 OneBot(NapCat) 方案：预留 openclaw-qq 插件配置
  if (GATEWAY_TOKEN || QQ_ID) {
    cfg.plugins = cfg.plugins || {}
    cfg.plugins.entries = cfg.plugins.entries || {}
    cfg.plugins.entries['openclaw-qq'] = {
      enabled: true,
      config: {
        napcatWs: process.env.NAPCAT_WS || 'ws://127.0.0.1:3001',
        napcatToken: GATEWAY_TOKEN,
        botQQ: QQ_ID,
        allowedUsers: [],
        allowedGroups: [],
      },
    }
  }

  fs.writeFileSync(cfgPath, JSON.stringify(cfg, null, 2), 'utf8')
  return cfgPath
}

function startOpenClaw() {
  const env = { ...process.env, HOME: DATA_DIR }
  const child = spawn('openclaw', ['gateway'], { stdio: 'inherit', env })

  child.on('exit', (code, signal) => {
    console.error(`[openclaw] exited: code=${code} signal=${signal}`)
    process.exit(code ?? 1)
  })
}

// 机器人原本的启动逻辑放在这里：生成配置并启动网关
writeOpenClawConfig()
startOpenClaw()

// 必须有的保活接口
app.get('/', (req, res) => {
  res.send('OpenClaw Bot is running!')
})

app.listen(port, '0.0.0.0', () => {
  console.log(`Keep-alive server is listening on port ${port}`)
})

