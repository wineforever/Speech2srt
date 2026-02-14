# Speech2SRT

一个本地音频转字幕工具，支持 Web UI 与 Windows 桌面 GUI（EXE）。

## Features

- 多 ASR 引擎：`BCut接口`（默认）、`JianYing接口`、`KuaiShou接口`、`Qwen3本地模型`
- 输出格式：`SRT`、`TXT`
- 支持裁剪起点、语言指定、进度轮询、结果预览、下载
- 任务完成提示音：使用项目根目录 `Sound.mp3`
- 一键启动脚本：`start_speech2srt.bat`
- Windows 桌面 GUI 封装：`desktop_gui.py` + `PyInstaller` 打包为 `.exe`

## Project Layout

```text
speech2srt/
├─ backend/                  # Flask API
│  ├─ app/
│  └─ run.py
├─ frontend/                 # React + Vite
├─ desktop/
│  ├─ build_exe.bat          # 打包 EXE
│  ├─ requirements-desktop.txt
│  └─ run_desktop_dev.bat
├─ Sound.mp3                 # 任务完成提示音
├─ speech2srt.ini            # 主配置
├─ start_speech2srt.bat      # 一键启动前后端
└─ desktop_gui.py            # 桌面 GUI 启动器
```

## Requirements

- Python 3.9+
- Node.js 18+
- FFmpeg
- Windows（打包 EXE 场景）

## Quick Start

### 1) 安装依赖

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

### 2) 配置 `speech2srt.ini`

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

- `backend_python`：若填写，优先使用这个 Python 路径
- `backend_conda_env`：若 `backend_python` 为空，则使用 `<conda_env>\python.exe`
- `asr_engine`：默认引擎（当前推荐 `bcut`）

### 3) 启动

方式 A：双击 `start_speech2srt.bat`（推荐）

方式 B：手动启动

```powershell
cd backend
python run.py
```

```powershell
cd frontend
npm run dev
```

Web UI 默认地址：`http://localhost:3000`

## Completion Sound

- 前端在任务完成时请求：`GET /api/assets/completion-sound`
- 后端优先读取环境变量 `SPEECH2SRT_SOUND_FILE`
- 未设置时默认读取项目根目录 `Sound.mp3`

如果要替换音效，直接替换根目录同名文件 `Sound.mp3` 即可。

## API (Core)

- `POST /api/upload`：上传音频
- `POST /api/process`：创建任务（可传 `asr_engine`）
- `GET /api/status/<job_id>`：查询任务
- `GET /api/download/<filename>`：下载产物
- `GET /api/asr-engines`：获取可选引擎与默认值
- `GET /api/assets/completion-sound`：获取任务完成提示音

`/api/process` 示例：

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

## Windows Desktop GUI (EXE)

### 本地开发运行

```powershell
python desktop_gui.py
```

或双击：

`desktop/run_desktop_dev.bat`

### 打包 EXE

双击：

`desktop/build_exe.bat`

产物：

`dist/Speech2SRT.exe`

说明：

- 打包脚本会先构建 `frontend/dist`
- EXE 内置前端静态资源、`speech2srt.ini`、`Sound.mp3`
- 桌面 GUI 仍然调用同一套 Flask API，WebUI 功能保持一致

## Troubleshooting

- 后端启动失败：
  - 检查 `speech2srt.ini` 中 `backend_python` / `backend_conda_env`
  - 检查 `pip install -r backend/requirements.txt` 是否完整
- 前端无法请求后端：
  - 确认 `http://localhost:5000/api/health` 可访问
- 在线接口失败：
  - `BCut/JianYing/KuaiShou` 依赖公网，可能受网络和策略影响
- 本地模型失败：
  - 检查 `asr_model_path` 是否正确、`torch` 与 CUDA 环境是否匹配
