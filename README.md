# Speech2SRT

> Local-first audio transcription and subtitle generation with a modern Web UI.

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)](#environment)
[![Node.js](https://img.shields.io/badge/Node.js-18%2B-339933?logo=node.js&logoColor=white)](#environment)
[![Flask](https://img.shields.io/badge/Backend-Flask-000000?logo=flask&logoColor=white)](#architecture)
[![React](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react&logoColor=black)](#architecture)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](#license)

Speech2SRT 是一个面向本地部署的音频转字幕工具，支持多 ASR 引擎、任务队列、进度跟踪与 SRT/TXT 导出。

## Highlights

- 多 ASR 引擎可选：`BCut接口`（默认）、`JianYing接口`、`KuaiShou接口`、`Qwen3本地模型`
- Web UI 工作流：上传 -> 参数设置 -> 后台任务 -> 结果下载
- 输出格式：`SRT` + `TXT`
- 支持完成提示音：根目录 `Sound.mp3`
- 支持配置覆盖：`INI > ENV > CLI`
- 提供 Windows 一键启动脚本：`start_speech2srt.bat`

## Screenshot

你可以在这里放首页截图（建议文件：`docs/screenshot-home.png`）：

```md
![Speech2SRT Home](docs/screenshot-home.png)
```

## Architecture

```text
speech2srt/
├─ backend/                  # Flask API
│  ├─ app/
│  ├─ requirements.txt
│  └─ run.py
├─ frontend/                 # React + Vite
├─ Sound.mp3                 # 任务完成提示音
├─ speech2srt.ini            # 主配置文件
├─ start_speech2srt.bat      # 一键启动（前后端）
└─ README.md
```

## Environment

- Python 3.9+
- Node.js 18+
- FFmpeg（音频处理依赖）

## Quick Start

### 1. Install dependencies

Backend:

```powershell
cd backend
pip install -r requirements.txt
```

Frontend:

```powershell
cd frontend
npm install
```

### 2. Configure `speech2srt.ini`

```ini
[runtime]
backend_conda_env = F:\miniconda\envs\unsloth
backend_python =

[asr]
asr_engine = bcut
asr_model_path = F:/Models/Qwen/Qwen3-ASR-0.6B
```

说明：

- `backend_python`：若填写，优先使用这个 Python 可执行文件
- `backend_conda_env`：若 `backend_python` 为空，则回退为 `<env>\python.exe`
- `asr_engine`：默认引擎，推荐 `bcut`

### 3. Start services

推荐直接双击根目录：

`start_speech2srt.bat`

该脚本会：

- 启动后端（自动读取 `speech2srt.ini` runtime 配置）
- 启动前端
- 自动打开 `http://localhost:3000`

手动方式：

```powershell
cd backend
python run.py
```

```powershell
cd frontend
npm run dev
```

## ASR Engines

| Engine ID | UI Name | Type | Notes |
|---|---|---|---|
| `bcut` | BCut接口 | Online | 默认引擎 |
| `jianying` | JianYing接口 | Online | 依赖公网 |
| `kuaishou` | KuaiShou接口 | Online | 依赖公网 |
| `qwen3_local` | Qwen3本地模型 | Local | 需本地模型路径 |

## Core API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/upload` | 上传音频 |
| `POST` | `/api/process` | 创建处理任务 |
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

## Completion Sound

任务完成后，前端会请求：

- `GET /api/assets/completion-sound`

后端按以下顺序查找音频：

1. 环境变量 `SPEECH2SRT_SOUND_FILE`
2. 项目根目录 `Sound.mp3`
3. 当前工作目录 `Sound.mp3`

如果你想替换音效，直接替换根目录同名文件 `Sound.mp3` 即可。

## Configuration Priority

配置优先级（高 -> 低）：

1. 命令行参数（CLI）
2. 环境变量（ENV）
3. `speech2srt.ini`
4. 代码默认值

## Troubleshooting

### 后端启动失败

- 检查 `speech2srt.ini` 的 `backend_python` / `backend_conda_env`
- 确认依赖安装完成：`pip install -r backend/requirements.txt`

### 前端无法请求后端

- 检查 `http://localhost:5000/api/health` 是否可访问
- 确认前端运行在 `http://localhost:3000`

### 在线引擎失败

- `BCut/JianYing/KuaiShou` 依赖公网，可能受网络和接口策略影响

### 本地模型失败

- 检查 `asr_model_path` 路径
- 检查 `torch` 与 CUDA 环境匹配关系

## Roadmap

- [ ] 批量文件处理与批量下载
- [ ] 更细粒度的字幕断句参数
- [ ] 多语言 UI

## Contributing

欢迎提交 Issue / PR。建议在提交前完成：

```powershell
cd frontend
npm run build
```

```powershell
python -m compileall backend/app backend/run.py
```

## License

MIT
