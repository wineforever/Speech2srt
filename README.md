# 🎤 Speech2SRT - 智能语音转字幕工具

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![Node.js Version](https://img.shields.io/badge/node.js-18%2B-green)
![Flask](https://img.shields.io/badge/Flask-3.0.0-blue)
![React](https://img.shields.io/badge/React-18.2.0-61dafb)
![License](https://img.shields.io/badge/license-MIT-yellow)

**一个基于深度学习的自动语音识别(ASR)系统，可将音频文件转换为SRT/TXT字幕格式，使用Qwen3-ASR-0.6B模型提供高精度转录服务。**

---

## ✨ 核心功能

- 🎯 **高精度语音识别** - 基于Qwen3-ASR-0.6B模型，支持中英文混合识别
- 📁 **多格式支持** - 支持WAV、MP3等常见音频格式
- 📝 **双字幕输出** - 同时生成SRT字幕文件和TXT文本文件
- ⚡ **实时处理** - 支持音频分块处理，优化长音频识别
- 🌐 **Web界面** - 现代化的React前端，直观易用的操作界面
- 🔧 **参数可调** - 提供丰富的处理参数配置选项
- 📊 **进度显示** - 实时显示处理进度和状态

## 🏗️ 项目架构

```
speech2srt/
├── backend/           # Flask后端服务
│   ├── app/          # 核心应用代码
│   │   ├── asr_service.py      # ASR服务模块
│   │   ├── subtitle_generator.py # 字幕生成器
│   │   ├── audio_processor.py   # 音频处理器
│   │   ├── routes.py           # API路由
│   │   └── config.py           # 配置管理
│   ├── uploads/      # 上传文件存储
│   ├── outputs/      # 处理结果存储
│   └── run.py        # 应用启动入口
├── frontend/         # React前端应用
│   ├── src/
│   │   ├── pages/HomePage.jsx    # 主页面
│   │   ├── components/           # 可复用组件
│   │   └── services/api.js       # API服务
│   └── package.json  # 前端依赖配置
└── README.md         # 项目说明文档
```

## 📋 系统要求

| 组件 | 最低版本 | 推荐版本 | 验证命令 |
|------|----------|----------|----------|
| Python | 3.9 | 3.10+ | `python --version` |
| Node.js | 18.0 | 20.0+ | `node --version` |
| FFmpeg | 4.0 | 5.0+ | `ffmpeg -version` |
| 内存 | 4GB | 8GB+ | - |
| 存储空间 | 5GB | 10GB+ | - |

**GPU支持（可选但推荐）**：
- NVIDIA GPU（支持CUDA 11.8+）
- 至少4GB VRAM
- 已安装对应版本的PyTorch with CUDA

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone https://github.com/yourusername/speech2srt.git
cd speech2srt
```

### 2. 后端环境配置
```bash
# 进入后端目录
cd backend

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 前端环境配置
```bash
# 返回项目根目录
cd ..

# 进入前端目录
cd frontend

# 安装依赖
npm install
```

### 4. 下载ASR模型
```bash
# 使用ModelScope下载（推荐）
modelscope download --model Qwen/Qwen3-ASR-0.6B --local_dir "F:\Models\Qwen\Qwen3-ASR-0.6B"

# 或者使用Hugging Face
# huggingface-cli download Qwen/Qwen3-ASR-0.6B --local-dir "F:\Models\Qwen\Qwen3-ASR-0.6B"
```

**注意**：如果模型路径不同，请修改`backend/app/config.py`中的`DEFAULT_MODEL_PATH`变量。

### 5. 启动后端服务
```bash
# 确保在backend目录下
cd backend

# 激活虚拟环境（如果尚未激活）
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# 启动Flask应用
python run.py
```
后端服务将在 `http://localhost:5000` 启动。

### 6. 启动前端服务
```bash
# 在新终端中，进入frontend目录
cd frontend

# 启动开发服务器
npm run dev
```
前端服务将在 `http://localhost:3000` 启动。

### 7. 访问应用
打开浏览器，访问 `http://localhost:3000` 即可开始使用。

## ⚙️ 环境变量配置

系统支持以下环境变量进行配置：

| 变量名 | 默认值 | 描述 | 类型 | 是否必需 |
|--------|--------|------|------|----------|
| `ASR_MODEL_PATH` | `F:\\Models\\Qwen\\Qwen3-ASR-0.6B` | ASR模型路径 | 字符串 | 是 |
| `ASR_DEVICE` | `cuda:0` | 推理设备（cuda:0 或 cpu） | 字符串 | 否 |
| `ASR_DTYPE` | `bfloat16` | 模型精度（bfloat16/float16/float32） | 字符串 | 否 |
| `ASR_LOCAL_FILES_ONLY` | `True` | 仅使用本地模型文件 | 布尔值 | 否 |
| `ASR_MAX_BATCH_SIZE` | `32` | 最大批处理大小 | 整数 | 否 |
| `ASR_MAX_NEW_TOKENS` | `2048` | 最大生成token数 | 整数 | 否 |
| `ASR_CHUNK_SECONDS` | `60` | 音频分块大小（秒），0为不分块 | 浮点数 | 否 |
| `ASR_UNLOAD_AFTER_TASK` | `True` | 任务完成后卸载模型 | 布尔值 | 否 |
| `ASR_TRUST_REMOTE_CODE` | `True` | 信任远程代码 | 布尔值 | 否 |
| `SUBTITLE_MAX_CHARS` | `60` | 每行字幕最大字符数 | 整数 | 否 |
| `SUBTITLE_MIN_DURATION` | `0.4` | 字幕最小持续时间（秒） | 浮点数 | 否 |
| `PREVIEW_MAX_CHARS` | `8000` | 预览最大字符数 | 整数 | 否 |
| `PREVIEW_MAX_SEGMENTS` | `200` | 预览最大段落数 | 整数 | 否 |
| `MAX_AUDIO_DURATION` | `0` | 最大音频时长（秒），0为无限制 | 浮点数 | 否 |
| `MAX_CONCURRENT_TASKS` | `3` | 最大并发任务数 | 整数 | 否 |
| `MAX_CONTENT_LENGTH_MB` | `100` | 最大上传文件大小（MB） | 整数 | 否 |
| `SUPPORTED_FORMATS` | `wav,mp3` | 支持的音频格式 | 字符串 | 否 |

**配置示例**（Windows PowerShell）：
```powershell
$env:ASR_DEVICE="cpu"
$env:ASR_MAX_BATCH_SIZE=16
$env:MAX_CONCURRENT_TASKS=2
python run.py
```

## 📡 API接口文档

### 文件上传
```http
POST /api/upload
```
**请求**：`multipart/form-data`格式，包含音频文件
**响应**：
```json
{
  "filename": "processed_1234567890.wav",
  "original_name": "audio.wav",
  "size": 1024000,
  "duration": 120.5
}
```

### 处理音频
```http
POST /api/process
```
**请求**：
```json
{
  "filename": "processed_1234567890.wav",
  "params": {
    "max_chars": 60,
    "min_duration": 0.4
  }
}
```
**响应**：
```json
{
  "job_id": "abc123def456",
  "status": "processing",
  "message": "任务已开始处理"
}
```

### 查询任务状态
```http
GET /api/status/<job_id>
```
**响应**：
```json
{
  "job_id": "abc123def456",
  "status": "completed",
  "progress": 100,
  "result": {
    "srt_filename": "processed_1234567890.srt",
    "txt_filename": "processed_1234567890.txt",
    "word_count": 1250
  }
}
```

### 下载文件
```http
GET /api/download/<filename>
```
**响应**：文件下载

### 预览字幕
```http
GET /api/preview/<filename>
```
**响应**：字幕文本内容

## 🎯 使用指南

### 基本使用流程
1. **上传音频文件**：通过Web界面选择音频文件（WAV/MP3格式）
2. **配置参数**：根据需要调整字幕生成参数
3. **开始处理**：点击"开始转换"按钮启动语音识别
4. **查看进度**：实时查看处理进度和状态
5. **下载结果**：处理完成后下载SRT和TXT文件

### 参数说明
- **每行最大字符数**：控制字幕每行的文本长度
- **最小持续时间**：控制字幕在屏幕上显示的最短时间
- **音频分块大小**：长音频分块处理的时长（秒）

## 📸 使用示例

### 示例1：基本使用
1. **准备音频文件**：确保你有一个WAV或MP3格式的音频文件
2. **打开Web界面**：访问 `http://localhost:3000`
3. **上传文件**：点击"选择文件"按钮，选择你的音频文件
4. **调整参数**（可选）：
   - 每行最大字符数：60（默认）
   - 最小持续时间：0.4秒（默认）
   - 音频分块大小：60秒（默认，0为不分块）
5. **开始转换**：点击"开始转换"按钮
6. **等待处理**：查看实时进度，处理时间取决于音频长度和硬件性能
7. **下载结果**：处理完成后，下载SRT和TXT文件

### 示例2：命令行API调用
如果你希望通过命令行直接使用API：

```bash
# 1. 上传音频文件
curl -X POST -F "file=@audio.wav" http://localhost:5000/api/upload

# 响应示例：
# {"filename": "processed_1234567890.wav", "original_name": "audio.wav", "size": 1024000, "duration": 120.5}

# 2. 处理音频
curl -X POST -H "Content-Type: application/json" \
  -d '{"filename": "processed_1234567890.wav", "params": {"max_chars": 60, "min_duration": 0.4}}' \
  http://localhost:5000/api/process

# 响应示例：
# {"job_id": "abc123def456", "status": "processing", "message": "任务已开始处理"}

# 3. 查询处理状态
curl http://localhost:5000/api/status/abc123def456

# 4. 下载结果文件
curl -O http://localhost:5000/api/download/processed_1234567890.srt
curl -O http://localhost:5000/api/download/processed_1234567890.txt
```

### 示例3：批量处理脚本
创建一个Python脚本批量处理多个音频文件：

```python
import requests
import os
import time

def process_audio_file(file_path, api_base="http://localhost:5000"):
    """处理单个音频文件并返回结果"""
    
    # 1. 上传文件
    with open(file_path, 'rb') as f:
        response = requests.post(f"{api_base}/api/upload", files={'file': f})
    upload_result = response.json()
    filename = upload_result['filename']
    
    # 2. 开始处理
    process_data = {
        'filename': filename,
        'params': {'max_chars': 60, 'min_duration': 0.4}
    }
    response = requests.post(f"{api_base}/api/process", json=process_data)
    process_result = response.json()
    job_id = process_result['job_id']
    
    # 3. 轮询状态
    while True:
        response = requests.get(f"{api_base}/api/status/{job_id}")
        status_result = response.json()
        
        if status_result['status'] == 'completed':
            # 4. 下载结果
            srt_response = requests.get(f"{api_base}/api/download/{status_result['result']['srt_filename']}")
            txt_response = requests.get(f"{api_base}/api/download/{status_result['result']['txt_filename']}")
            
            # 保存文件
            with open(f"{file_path}.srt", 'wb') as f:
                f.write(srt_response.content)
            with open(f"{file_path}.txt", 'wb') as f:
                f.write(txt_response.content)
                
            return True
            
        elif status_result['status'] == 'failed':
            print(f"处理失败: {status_result.get('error', '未知错误')}")
            return False
        
        time.sleep(2)  # 等待2秒后再次查询

# 批量处理目录中的所有音频文件
audio_dir = "path/to/audio/files"
for file in os.listdir(audio_dir):
    if file.endswith(('.wav', '.mp3')):
        print(f"处理文件: {file}")
        process_audio_file(os.path.join(audio_dir, file))
```

### 界面截图说明
由于无法提供实际截图，以下是界面区域描述：

1. **文件上传区**：位于页面顶部，包含文件选择按钮和拖放区域
2. **参数设置区**：提供字幕生成参数的可调节选项
3. **处理控制区**：包含"开始转换"按钮和进度显示
4. **结果展示区**：显示处理状态、预览字幕和下载链接

## 🔧 故障排除

### 常见问题

**Q: 启动后端服务时出现模型加载错误**
A: 确保模型已正确下载，且路径配置正确。检查`ASR_MODEL_PATH`环境变量或`config.py`中的默认路径。

**Q: 前端无法连接到后端API**
A: 检查后端服务是否正常运行（`http://localhost:5000`），并确保CORS配置正确。

**Q: 音频处理速度慢**
A: 尝试启用GPU加速（设置`ASR_DEVICE=cuda:0`），或减少`ASR_MAX_BATCH_SIZE`。

**Q: 内存不足错误**
A: 减少`ASR_MAX_BATCH_SIZE`，或启用`ASR_UNLOAD_AFTER_TASK=True`。

**Q: FFmpeg相关错误**
A: 确保FFmpeg已正确安装并添加到系统PATH中。

### 日志查看
- 后端日志：查看控制台输出或Flask日志文件
- 前端日志：使用浏览器开发者工具（F12）查看控制台

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork本仓库
2. 创建功能分支（`git checkout -b feature/AmazingFeature`）
3. 提交更改（`git commit -m 'Add some AmazingFeature'`）
4. 推送到分支（`git push origin feature/AmazingFeature`）
5. 开启Pull Request

### 代码规范
- Python代码遵循PEP8规范
- JavaScript/React代码使用ESLint配置
- 提交信息使用约定式提交

## 📄 许可证

本项目采用MIT许可证。详见[LICENSE](LICENSE)文件（如有）。

## 🙏 致谢

- [Qwen团队](https://github.com/QwenLM) - 提供优秀的Qwen3-ASR模型
- [ModelScope](https://modelscope.cn) - 模型托管和下载平台
- [Flask](https://flask.palletsprojects.com/) - 轻量级Web框架
- [React](https://react.dev/) - 前端JavaScript库

---

**Speech2SRT** - 让语音转字幕变得更简单！ 🎧➡️📝

如有问题或建议，请提交Issue或联系维护者。