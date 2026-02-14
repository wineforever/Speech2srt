# Speech2SRT

本项目用于将音频文件转写为字幕，提供 Web UI 与后端 API，支持多 ASR 引擎与任务队列。

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)](#环境要求)
[![Node.js](https://img.shields.io/badge/Node.js-18%2B-339933?logo=node.js&logoColor=white)](#环境要求)
[![Flask](https://img.shields.io/badge/Backend-Flask-black?logo=flask)](#项目结构)
[![React](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react&logoColor=black)](#项目结构)

---

## 核心特性

- 多 ASR 引擎：`BCut接口`（默认）、`JianYing接口`、`KuaiShou接口`、`Qwen3本地模型`
- 输出格式：`SRT`、`TXT`
- 支持任务队列、进度轮询、结果预览与下载
- 任务完成提示音：根目录 `Sound.mp3`
- 支持配置覆盖：`CLI > ENV > INI`
- Windows 一键启动脚本：`start_speech2srt.bat`

## 启动性能优化（本次更新）

- 默认引擎为 `bcut`（不使用 Qwen3 大模型）
- 后端进程启动时**不导入** `torch` 和 `qwen_asr`
- 仅在以下条件同时满足时才开始导入 PyTorch：
  1. 任务引擎选择 `qwen3_local`
  2. 任务真正开始转写

这能明显缩短后端冷启动时间，尤其是 Windows 服务器场景。

---

## 项目结构

```text
speech2srt/
├─ backend/                  # Flask 后端
│  ├─ app/
│  ├─ requirements.txt
│  └─ run.py
├─ frontend/                 # React + Vite 前端
├─ Sound.mp3                 # 完成提示音
├─ speech2srt.ini            # 项目配置
├─ start_speech2srt.bat      # 一键启动前后端
└─ README.md
```

---

## 环境要求

- Python 3.9+
- Node.js 18+
- FFmpeg

---

## 本地开发快速开始

### 1. 安装依赖

后端：

```powershell
cd backend
pip install -r requirements.txt
```

前端：

```powershell
cd frontend
npm install
```

### 2. 配置 `speech2srt.ini`

示例：

```ini
[runtime]
backend_conda_env = F:\miniconda\envs\unsloth
backend_python =

[asr]
asr_engine = bcut
asr_model_path = F:/Models/Qwen/Qwen3-ASR-0.6B
```

说明：

- `backend_python`：若填写则优先使用该 Python 可执行文件
- `backend_conda_env`：若 `backend_python` 为空，则使用 `<env>\python.exe`
- `asr_engine`：默认引擎，建议保留 `bcut`

### 3. 启动

推荐直接双击：

`start_speech2srt.bat`

该脚本会自动：

- 启动后端
- 启动前端开发服务器
- 打开 `http://localhost:3000`

---

## Windows 服务器部署（推荐流程）

以下流程适合生产/长期运行，不依赖前端开发服务器。

### Step 1. 服务器准备

1. 安装 Miniconda（或你已有 Python 发行版）
2. 安装 Node.js LTS
3. 安装 FFmpeg，并加入系统 PATH
4. 拉取项目代码到固定目录，例如：`D:\apps\speech2srt`

### Step 2. 创建后端运行环境

```powershell
conda create -n speech2srt python=3.10 -y
conda activate speech2srt
cd D:\apps\speech2srt\backend
pip install -r requirements.txt
```

说明：如果你长期只用在线引擎（`bcut/jianying/kuaishou`），即使安装了 `torch`，后端启动也不会提前导入。

### Step 3. 构建前端静态文件

```powershell
cd D:\apps\speech2srt\frontend
npm ci
npm run build
```

构建后会生成 `frontend\dist`。  
后端会自动托管该目录（无需 `npm run dev`）。

### Step 4. 配置生产参数

编辑 `speech2srt.ini`：

```ini
[runtime]
backend_conda_env = F:\miniconda\envs\speech2srt
backend_python =

[asr]
asr_engine = bcut
```

### Step 5. 启动后端（生产方式）

```powershell
cd D:\apps\speech2srt\backend
F:\miniconda\envs\speech2srt\python.exe run.py --host 0.0.0.0 --port 5000
```

访问地址：

- 同机：`http://127.0.0.1:5000`
- 局域网：`http://<server-ip>:5000`

### Step 6. 注册为 Windows 服务（可选，推荐）

建议使用 NSSM（Non-Sucking Service Manager）：

```powershell
nssm install Speech2SRT
```

配置：

- `Application`：`F:\miniconda\envs\speech2srt\python.exe`
- `Startup directory`：`D:\apps\speech2srt\backend`
- `Arguments`：`run.py --host 0.0.0.0 --port 5000`

然后：

```powershell
nssm start Speech2SRT
```

### Step 7. 防火墙与反向代理（可选）

- 开放 `5000` 端口（或仅内网开放）
- 若对外提供服务，建议通过 Nginx/IIS 做 HTTPS 反向代理

---

## 完成提示音

- 前端请求：`GET /api/assets/completion-sound`
- 后端查找顺序：
  1. `SPEECH2SRT_SOUND_FILE` 环境变量
  2. 项目根目录 `Sound.mp3`
  3. 当前工作目录 `Sound.mp3`

你可以直接替换根目录 `Sound.mp3` 来更换提示音。

---

## API 概览

| Method | Endpoint | 说明 |
|---|---|---|
| `POST` | `/api/upload` | 上传音频 |
| `POST` | `/api/process` | 创建任务 |
| `GET` | `/api/status/<job_id>` | 查询任务状态 |
| `GET` | `/api/download/<filename>` | 下载结果 |
| `GET` | `/api/asr-engines` | 获取引擎列表 |
| `GET` | `/api/assets/completion-sound` | 获取完成提示音 |
| `GET` | `/api/health` | 健康检查 |

`/api/process` 请求示例：

```json
{
  "filename": "demo.wav",
  "original_filename": "demo.wav",
  "crop_seconds": 0,
  "output_formats": {
    "srt": true,
    "txt": true
  },
  "language": null,
  "asr_engine": "bcut"
}
```

---

## 常见问题

### 1) 后端启动失败

- 检查 `speech2srt.ini` 的 `backend_python` / `backend_conda_env`
- 检查依赖是否完整：`pip install -r backend/requirements.txt`

### 2) 前端无法访问后端

- 检查 `http://localhost:5000/api/health`
- 开发模式确认前端在 `http://localhost:3000`

### 3) 在线引擎失败

- `BCut/JianYing/KuaiShou` 依赖公网，可能受网络与接口策略影响

### 4) Qwen3 本地模型失败

- 检查 `asr_model_path` 是否正确
- 检查 `torch` 与 CUDA/驱动兼容性

---

## License

MIT
