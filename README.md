# Speech2SRT CLI

将音频通过语音识别接口转写为字幕。程序默认使用 BCut 在线接口，直接处理完整原始音频，不进行裁剪，并同时生成 SRT 字幕和 TXT 文本。

## 功能

- 命令行直接转写单个音频文件
- 默认使用 `bcut`，也可切换 `jianying`、`kuaishou` 或 `qwen3_local`
- 不裁剪、不重编码、不额外保存音频副本
- 每次固定输出同名 `.srt` 和 `.txt`
- 支持 WAV、MP3，格式范围可在 `speech2srt.ini` 中配置
- CLI 单一入口，不包含 Web 服务和前端

## 项目结构

```text
Speech2SrtCLI/
├─ cli.py                     # CLI 入口
├─ backend/
│  ├─ app/
│  │  ├─ asr_engines.py          # BCut、剪映、快手接口
│  │  ├─ asr_service.py          # ASR 引擎调度与本地模型懒加载
│  │  ├─ audio_processor.py      # 音频校验与本地模型分片
│  │  ├─ subtitle_generator.py   # SRT/TXT 生成
│  │  ├─ config.py               # INI、环境变量与运行参数
│  │  └─ utils.py                # 文件名与时间格式工具
│  └─ requirements.txt
├─ speech2srt.ini                # 默认配置
├─ requirements.txt              # 依赖入口
└─ README.md
```

## 环境要求

- Python 3.9+
- FFmpeg，并确保 `ffmpeg` 可从 `PATH` 调用
- BCut、剪映和快手引擎需要访问公网

## 安装

建议创建虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

`pydub` 负责读取音频，MP3 等格式需要 FFmpeg。`torch` 和 `qwen-asr` 仅在选择 `qwen3_local` 时按需加载。

## 使用

在项目根目录执行：

```powershell
python cli.py .\audio.mp3
```

默认输出到 `backend\outputs`：

```text
backend\outputs\audio.srt
backend\outputs\audio.txt
```

程序直接提交输入音频，不执行裁剪，也不会生成处理后的音频副本。

### 指定输出目录

```powershell
python cli.py .\audio.wav --output-dir .\results
```

### 指定语言

```powershell
python cli.py .\audio.mp3 --language zh
```

### 切换 ASR 引擎

```powershell
python cli.py .\audio.mp3 --asr-engine jianying
python cli.py .\audio.mp3 --asr-engine kuaishou
python cli.py .\audio.mp3 --asr-engine qwen3_local
```

### 调整字幕长度

```powershell
python cli.py .\audio.mp3 --subtitle-max-chars 40 --subtitle-min-duration 0.5
```

### 查看帮助

```powershell
python cli.py --help
```

## CLI 参数

| 参数 | 默认值 | 说明 |
|---|---:|---|
| `input` | 必填 | 输入音频路径 |
| `-o, --output-dir` | 配置中的 `output_dir` | SRT/TXT 输出目录 |
| `--asr-engine` | `bcut` | ASR 引擎 |
| `--language` | 自动识别 | 可选语言代码 |
| `--config` | `speech2srt.ini` | INI 配置路径 |
| `--subtitle-max-chars` | `60` | 单条字幕最大字符数 |
| `--subtitle-min-duration` | `0.4` | 单条字幕最小时长（秒） |

参数覆盖顺序为：命令行参数 > 环境变量 > `speech2srt.ini` > 内置默认值。

## 配置

默认配置文件为 `speech2srt.ini`。CLI 常用配置：

```ini
[paths]
output_dir = backend/outputs

[service]
supported_formats = wav,mp3
max_audio_duration = 0

[asr]
asr_engine = bcut
asr_chunk_seconds = 60
asr_unload_after_task = true

[subtitle]
subtitle_max_chars = 60
subtitle_min_duration = 0.4
```

- `max_audio_duration = 0` 表示不限制时长。
- `asr_engine = bcut` 是默认在线引擎。
- 在线引擎使用原始输入文件，不裁剪；`qwen3_local` 会按 `asr_chunk_seconds` 分片推理。

## 输出说明

假设输入文件为 `meeting.mp3`，输出文件为：

- `meeting.srt`：带时间轴的字幕
- `meeting.txt`：每条字幕一行的纯文本

若同名文件已存在，CLI 会覆盖同名 SRT/TXT。需要保留旧结果时，请指定不同的输出目录或先重命名已有文件。

## 常见问题

### FFmpeg 未找到

安装 FFmpeg 并将其 `bin` 目录加入 `PATH`，然后重新打开终端。

### BCut 转写失败

确认网络可用后重试。在线接口属于非官方、非稳定依赖，其协议或可用性可能变化。

### 输入格式不支持

在 `speech2srt.ini` 的 `supported_formats` 中添加扩展名，并确认 FFmpeg 能解码该格式。

### 本地模型失败

使用 `qwen3_local` 时，检查 `asr_model_path`、PyTorch、CUDA 驱动和设备配置。

## License

MIT
