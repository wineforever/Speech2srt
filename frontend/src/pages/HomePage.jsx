import React, { useEffect, useRef, useState } from 'react'
import FileUpload from '../components/FileUpload.jsx'
import AudioPlayer from '../components/AudioPlayer.jsx'
import ParameterSettings from '../components/ParameterSettings.jsx'
import ProgressBar from '../components/ProgressBar.jsx'
import DownloadSection from '../components/DownloadSection.jsx'
import api from '../services/api.js'

const initialSettings = {
  cropSeconds: 5.5,
  outputFormats: { srt: true, txt: true },
  language: ''
}

const HomePage = () => {
  const [uploadedFile, setUploadedFile] = useState(null)
  const [uploadedFilename, setUploadedFilename] = useState('')
  const [uploadedDisplayName, setUploadedDisplayName] = useState('')
  const [audioUrl, setAudioUrl] = useState('')
  const [settings, setSettings] = useState(initialSettings)
  const [isUploading, setIsUploading] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [progressMessage, setProgressMessage] = useState('')
  const [etaSeconds, setEtaSeconds] = useState(null)
  const [jobId, setJobId] = useState('')
  const [jobStatus, setJobStatus] = useState('')
  const [outputFiles, setOutputFiles] = useState(null)
  const [previews, setPreviews] = useState({})
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const pollingRef = useRef(null)
  const lastStatusRef = useRef('')
  const jobStartRef = useRef(null)

  const stopPolling = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
  }

  useEffect(() => () => stopPolling(), [])

  const playCompletionSound = () => {
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext
      if (!AudioContext) {
        return
      }
      const context = new AudioContext()
      const oscillator = context.createOscillator()
      const gainNode = context.createGain()
      oscillator.type = 'sine'
      oscillator.frequency.value = 880
      gainNode.gain.value = 0.1
      oscillator.connect(gainNode)
      gainNode.connect(context.destination)
      oscillator.start()
      oscillator.stop(context.currentTime + 0.25)
      oscillator.onended = () => context.close()
    } catch (err) {
      // ignore audio errors
    }
  }

  const startPolling = (id) => {
    stopPolling()
    const poll = async () => {
      try {
        const response = await api.getJobStatus(id)
        const data = response.data
        const nextProgress = data.progress || 0
        setJobStatus(data.status)
        setProgress(nextProgress)
        setProgressMessage(data.message || '')

        if (data.status === 'done') {
          setOutputFiles(data.output_files)
          setPreviews(data.previews || {})
          setIsProcessing(false)
          setSuccess('处理完成，可以下载结果')
          setEtaSeconds(null)
          jobStartRef.current = null
          if (lastStatusRef.current !== 'done') {
            playCompletionSound()
          }
          stopPolling()
        }

        if (data.status === 'failed') {
          setIsProcessing(false)
          setError(data.error || '处理失败')
          setEtaSeconds(null)
          jobStartRef.current = null
          stopPolling()
        }
        if (data.status === 'running' || data.status === 'queued') {
          if (!jobStartRef.current) {
            jobStartRef.current = Date.now()
          }
          if (nextProgress > 1) {
            const elapsed = (Date.now() - jobStartRef.current) / 1000
            const remaining = Math.max(0, (elapsed * (100 - nextProgress)) / nextProgress)
            setEtaSeconds(remaining)
          } else {
            setEtaSeconds(null)
          }
        }
        lastStatusRef.current = data.status
      } catch (err) {
        setIsProcessing(false)
        setError('获取任务状态失败')
        setEtaSeconds(null)
        jobStartRef.current = null
        stopPolling()
      }
    }

    poll()
    pollingRef.current = setInterval(poll, 1500)
  }

  const handleFileUpload = async (file) => {
    try {
      setError('')
      setSuccess('')
      setIsUploading(true)
      setUploadedFile(null)
      setUploadedFilename('')
      setUploadedDisplayName('')
      setAudioUrl('')
      setOutputFiles(null)
      setPreviews({})
      setEtaSeconds(null)
      setProgress(0)
      setProgressMessage('')
      setJobId('')
      setJobStatus('')
      lastStatusRef.current = ''
      jobStartRef.current = null
      stopPolling()

      const response = await api.uploadFile(file)
      const { filename } = response.data

      setUploadedFile(file)
      setUploadedFilename(filename)
      setUploadedDisplayName(file.name)
      setAudioUrl(api.previewAudio(filename))
      setSuccess('上传成功')
    } catch (err) {
      setError(err.response?.data?.error || '文件上传失败')
    } finally {
      setIsUploading(false)
    }
  }

  const handleSettingsChange = (newSettings) => {
    setSettings(newSettings)
  }

  const handleProcessAudio = async () => {
    if (!uploadedFilename) {
      setError('请先上传音频文件')
      return
    }

    try {
      setError('')
      setSuccess('')
      setIsProcessing(true)
      setOutputFiles(null)
      setPreviews({})
      setEtaSeconds(null)
      setProgress(0)
      setProgressMessage('任务已创建')

      const response = await api.createJob({
        filename: uploadedFilename,
        cropSeconds: settings.cropSeconds,
        outputFormats: settings.outputFormats,
        language: settings.language || null
      })

      const newJobId = response.data.job_id
      setJobId(newJobId)
      setJobStatus('queued')
      startPolling(newJobId)
    } catch (err) {
      setError(err.response?.data?.error || '创建处理任务失败')
      setIsProcessing(false)
    }
  }

  const handleDownload = async (filename) => {
    try {
      const response = await api.downloadFile(filename)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    } catch (err) {
      setError('文件下载失败')
    }
  }

  const handleReset = () => {
    stopPolling()
    setUploadedFile(null)
    setUploadedFilename('')
    setUploadedDisplayName('')
    setAudioUrl('')
    setSettings(initialSettings)
    setIsProcessing(false)
    setIsUploading(false)
    setProgress(0)
    setProgressMessage('')
    setJobId('')
    setJobStatus('')
    setOutputFiles(null)
    setPreviews({})
    setEtaSeconds(null)
    lastStatusRef.current = ''
    jobStartRef.current = null
    setError('')
    setSuccess('')
  }

  const showProgress = isProcessing || (jobStatus && jobStatus !== 'done' && jobStatus !== 'failed')

  return (
    <div className="page-shell">
      <div className="max-w-6xl mx-auto relative">
        <header className="panel fade-up">
          <div className="flex flex-col lg:flex-row gap-8 items-start">
            <div className="flex-1">
              <span className="badge">Local Qwen3-ASR</span>
              <h1 className="hero-title text-4xl md:text-5xl mt-4">音频处理与字幕生成</h1>
              <p className="text-slate-600 mt-3">
                本地模型驱动，支持裁剪、字幕断句和多格式导出，适合快速生成配套字幕。
              </p>
              <div className="mt-4 flex flex-wrap gap-3 text-sm text-slate-600">
                <div className="px-3 py-1 rounded-full bg-white/70 border border-slate-200">WAV / MP3</div>
                <div className="px-3 py-1 rounded-full bg-white/70 border border-slate-200">本地推理</div>
                <div className="px-3 py-1 rounded-full bg-white/70 border border-slate-200">SRT + TXT</div>
              </div>
            </div>
            <div className="panel panel-subtle min-w-[240px]">
              <p className="text-sm text-slate-600">任务状态</p>
              <p className="text-2xl font-display mt-2">{jobStatus || '就绪'}</p>
              <p className="text-xs text-slate-500 mt-2">{jobId ? `任务 ID: ${jobId.slice(0, 8)}` : '尚未开始处理'}</p>
            </div>
          </div>
        </header>

        <div className="mt-8 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="space-y-6">
            <FileUpload onFileUpload={handleFileUpload} disabled={isUploading || isProcessing} />
            {audioUrl && (
              <AudioPlayer
                audioUrl={audioUrl}
                filename={uploadedDisplayName || uploadedFilename}
                disabled={isProcessing}
              />
            )}
            <ParameterSettings
              onSettingsChange={handleSettingsChange}
              settings={settings}
              disabled={isProcessing || !uploadedFile}
            />
            <div className="panel panel-subtle">
              <span className="badge">Step 4</span>
              <h3 className="text-lg font-display mt-2">开始处理</h3>
              <p className="text-sm text-slate-600 mt-2">
                提交任务后会进入后台队列，进度自动刷新。
              </p>
              <div className="mt-4 flex flex-wrap gap-3">
                <button
                  className="bg-primary text-white px-6 py-2 rounded-full hover:opacity-90 transition"
                  onClick={handleProcessAudio}
                  disabled={isProcessing || isUploading || !uploadedFile}
                >
                  {isProcessing ? '处理中...' : '开始处理'}
                </button>
                <button
                  className="bg-white/80 border border-slate-200 text-slate-700 px-6 py-2 rounded-full hover:bg-white transition"
                  onClick={handleReset}
                  disabled={isProcessing || isUploading}
                >
                  重置
                </button>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            {(error || success) && (
              <div className="panel panel-subtle">
                {error && <p className="text-danger font-medium">{error}</p>}
                {success && <p className="text-primary font-medium">{success}</p>}
              </div>
            )}

            {showProgress && (
              <ProgressBar progress={progress} message={progressMessage} etaSeconds={etaSeconds} />
            )}

            {outputFiles && (
              <DownloadSection outputFiles={outputFiles} onDownload={handleDownload} />
            )}

            {previews?.srt?.content && (
              <div className="panel panel-subtle">
                <h3 className="text-lg font-display">SRT 预览</h3>
                <pre className="mt-3 max-h-72 overflow-y-auto whitespace-pre-wrap text-xs text-slate-700 bg-white/80 border border-slate-200 rounded-xl p-4">
                  {previews.srt.content}
                </pre>
                {previews.srt.truncated && (
                  <p className="text-xs text-slate-500 mt-2">内容较长，已截断显示。</p>
                )}
              </div>
            )}

            <div className="panel panel-subtle">
              <h3 className="text-lg font-display">运行提示</h3>
              <ul className="mt-3 space-y-2 text-sm text-slate-600 list-disc list-inside">
                <li>首次推理会加载模型，耗时略长。</li>
                <li>本地模型路径通过后端环境变量配置。</li>
                <li>建议在 5 分钟以内音频上测试以校验速度。</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default HomePage
