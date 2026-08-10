# Speech2SRT CLI

一个轻量、可扩展的音频转字幕命令行工具。输入音频文件，一次生成标准 `SRT` 字幕和纯文本 `TXT`；支持 BCut、剪映、快手在线识别接口，以及 Qwen3-ASR 本地模型。

> 默认使用 BCut 在线接口。在线引擎会把音频上传到对应的第三方服务，请勿处理不允许外传的敏感音频。相关接口并非官方稳定 API，可能随服务端协议变化而失效。

## 特性

- 一条命令生成同名 `.srt` 与 `.txt`
- 在线引擎直接识别原始音频，不裁剪、不重编码
- 在线与本地 ASR 引擎使用统一工作流
- INI、环境变量、命令行三级配置
- 本地 Qwen3-ASR 按需加载，可配置 CUDA、精度与分片时长
- 可安装 Python 包，同时兼容原有 `python cli.py` 用法
- 核心字幕与配置逻辑具备离线自动化测试

## 快速开始

### 1. 环境要求

- Python 3.9 或更高版本
- [FFmpeg](https://ffmpeg.org/download.html)，并确保 `ffmpeg` 可从 `PATH` 调用
- 在线引擎需要可访问对应服务的网络环境

### 2. 安装

```powershell
git clone https://github.com/wineforever/Speech2srt.git
cd Speech2srt
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

如需使用 Qwen3-ASR 本地模型，安装可选依赖：

```powershell
python -m pip install -e ".[local]"
```

也可以继续使用依赖文件：

```powershell
python -m pip install -r requirements.txt
# 本地模型额外依赖
python -m pip install -r requirements-local.txt
```

### 3. 转写音频

```powershell
speech2srt .\audio.mp3
```

未安装为命令时，以下两种入口效果相同：

```powershell
python -m speech2srt .\audio.mp3
python cli.py .\audio.mp3
```

默认生成：

```text
outputs/
├── audio.srt
└── audio.txt
```

## 常用示例

指定输出目录：

```powershell
speech2srt .\audio.wav --output-dir .\results
```

切换识别引擎：

```powershell
speech2srt .\audio.mp3 --asr-engine jianying
speech2srt .\audio.mp3 --asr-engine kuaishou
speech2srt .\audio.mp3 --asr-engine qwen3_local
```

指定语言并调整字幕长度：

```powershell
speech2srt .\audio.mp3 --language zh --subtitle-max-chars 40 --subtitle-min-duration 0.5
```

查看全部参数：

```powershell
speech2srt --help
```

## ASR 引擎

| 引擎 | 类型 | 默认安装可用 | 说明 |
|---|---|---:|---|
| `bcut` | 在线 | 是 | 默认引擎，使用非官方在线识别接口 |
| `jianying` | 在线 | 是 | 使用剪映相关的非官方在线接口 |
| `kuaishou` | 在线 | 是 | 使用快手相关的非官方在线接口 |
| `qwen3_local` | 本地 | 否 | 需要 `torch`、`qwen-asr` 与本地模型 |

在线引擎不进行音频分片。`qwen3_local` 会按照 `asr_chunk_seconds` 分片推理，并在完成后清理临时分片。

## 配置

默认配置文件是项目根目录的 [`speech2srt.ini`](speech2srt.ini)：

```ini
[paths]
output_dir = outputs

[service]
supported_formats = wav,mp3
max_audio_duration = 0

[asr]
asr_engine = bcut
asr_model_path = F:/Models/Qwen/Qwen3-ASR-0.6B
asr_device = cuda:0
asr_dtype = bfloat16
asr_chunk_seconds = 60
asr_unload_after_task = true

[subtitle]
subtitle_max_chars = 60
subtitle_min_duration = 0.4
```

- `max_audio_duration = 0`：不限制输入时长
- `asr_local_files_only = true`：只从本地路径加载 Qwen 模型
- `asr_unload_after_task = true`：任务后释放模型和显存
- 相对路径以配置文件所在目录为基准解析

配置优先级为：**命令行参数 > 环境变量 > INI 文件 > 内置默认值**。常用环境变量包括：

| 环境变量 | 对应配置 |
|---|---|
| `OUTPUT_DIR` | 输出目录 |
| `SUPPORTED_FORMATS` | 支持的扩展名，逗号分隔 |
| `MAX_AUDIO_DURATION` | 最大音频时长（秒） |
| `ASR_ENGINE` | 默认 ASR 引擎 |
| `ASR_MODEL_PATH` | 本地模型目录 |
| `ASR_DEVICE` | 推理设备，如 `cuda:0` 或 `cpu` |
| `ASR_DTYPE` | `bfloat16`、`float16` 或 `float32` |
| `ASR_CHUNK_SECONDS` | 本地模型分片时长 |
| `SUBTITLE_MAX_CHARS` | 单条字幕最大字符数 |
| `SUBTITLE_MIN_DURATION` | 单条字幕最小时长 |

## 项目架构

```text
Speech2SrtCLI/
├── speech2srt/
│   ├── cli.py                 # 参数解析、终端输出和退出码
│   ├── application.py         # 单次转写用例编排
│   ├── asr_service.py         # ASR 调度、本地模型生命周期和分片
│   ├── asr_engines.py         # 在线引擎适配器
│   ├── audio_processor.py     # 音频读取、校验和分片
│   ├── subtitle_generator.py  # 字幕拆分及 SRT/TXT 渲染
│   ├── config.py              # 配置加载与优先级
│   └── utils.py               # 文件名和时间格式工具
├── tests/                     # 离线测试
├── cli.py                     # 向后兼容入口
├── pyproject.toml             # 包元数据与命令注册
├── speech2srt.ini             # 默认配置
└── requirements*.txt          # 基础/本地模型依赖
```

`application.transcribe_file()` 是 CLI 与业务流程之间的稳定边界。新增入口（例如桌面应用或批处理器）时，可以直接调用它，无需模拟命令行参数。

## 开发与测试

```powershell
python -m pip install -e ".[dev]"
python -m pytest
```

不安装开发依赖时，也可用标准库运行测试：

```powershell
python -m unittest discover -s tests -v
```

## 常见问题

### 找不到 FFmpeg

安装 FFmpeg，将其 `bin` 目录加入 `PATH`，重新打开终端后运行 `ffmpeg -version` 确认。

### 输入格式不支持

在 `speech2srt.ini` 的 `supported_formats` 中加入扩展名，并确认 FFmpeg 可以解码该文件。

### 本地模型无法启动

确认已安装本地模型依赖，并检查 `asr_model_path`、CUDA 驱动、`asr_device` 与 `asr_dtype`。当 CUDA 不可用时，程序会退回 CPU，但速度通常明显下降。

### 在线接口转写失败

先确认网络可用后重试。由于在线引擎依赖非官方协议，服务端更新可能导致暂时不可用；对稳定性或隐私有严格要求时，请使用 `qwen3_local`。

## License

[MIT](LICENSE)
