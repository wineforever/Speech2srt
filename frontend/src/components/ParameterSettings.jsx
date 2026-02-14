import React, { useEffect, useMemo, useState } from 'react'

const fallbackEngines = [
  { id: 'bcut', label: 'BCut接口' },
  { id: 'jianying', label: 'JianYing接口' },
  { id: 'kuaishou', label: 'KuaiShou接口' },
  { id: 'qwen3_local', label: 'Qwen3本地模型' }
]

const ParameterSettings = ({ onSettingsChange, disabled, settings, engineOptions }) => {
  const [cropSeconds, setCropSeconds] = useState(5.5)
  const [language, setLanguage] = useState('')
  const [asrEngine, setAsrEngine] = useState('bcut')
  const [outputFormats, setOutputFormats] = useState({
    srt: true,
    txt: true
  })

  const engines = useMemo(() => {
    if (!Array.isArray(engineOptions) || engineOptions.length === 0) {
      return fallbackEngines
    }
    const normalized = engineOptions
      .map((item) => ({
        id: String(item.id || '').trim(),
        label: String(item.label || item.id || '').trim()
      }))
      .filter((item) => item.id && item.label)
    return normalized.length > 0 ? normalized : fallbackEngines
  }, [engineOptions])

  useEffect(() => {
    if (!settings) {
      return
    }
    if (typeof settings.cropSeconds === 'number') {
      setCropSeconds(settings.cropSeconds)
    }
    if (settings.language !== undefined) {
      setLanguage(settings.language || '')
    }
    if (settings.asrEngine !== undefined) {
      setAsrEngine(settings.asrEngine || '')
    }
    if (settings.outputFormats) {
      setOutputFormats(settings.outputFormats)
    }
  }, [settings])

  useEffect(() => {
    if (asrEngine || engines.length === 0) {
      return
    }
    const fallback = engines[0].id
    setAsrEngine(fallback)
    onSettingsChange({
      cropSeconds,
      outputFormats,
      language,
      asrEngine: fallback
    })
  }, [asrEngine, cropSeconds, engines, language, onSettingsChange, outputFormats])

  const emitChange = (next) => {
    onSettingsChange({
      cropSeconds,
      outputFormats,
      language,
      asrEngine,
      ...next
    })
  }

  const handleCropSecondsChange = (event) => {
    const value = parseFloat(event.target.value) || 0
    setCropSeconds(value)
    emitChange({ cropSeconds: value })
  }

  const handleAsrEngineChange = (event) => {
    const value = event.target.value
    setAsrEngine(value)
    emitChange({ asrEngine: value })
  }

  const handleFormatToggle = (format) => {
    const newFormats = {
      ...outputFormats,
      [format]: !outputFormats[format]
    }
    setOutputFormats(newFormats)
    emitChange({ outputFormats: newFormats })
  }

  const handleLanguageChange = (event) => {
    const value = event.target.value
    setLanguage(value)
    emitChange({ language: value })
  }

  return (
    <div className="panel panel-subtle">
      <span className="badge">Step 3</span>
      <h3 className="text-lg font-display mt-2">参数设置</h3>
      <div className="mt-5 space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">裁剪起点（秒）</label>
          <div className="flex flex-col gap-2">
            <input
              type="number"
              min="0"
              step="0.1"
              value={cropSeconds}
              onChange={handleCropSecondsChange}
              disabled={disabled}
            />
            <span className="text-xs text-slate-600">0 表示不裁剪</span>
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">ASR 引擎</label>
          <select
            value={asrEngine}
            onChange={handleAsrEngineChange}
            disabled={disabled}
          >
            {engines.map((engine) => (
              <option key={engine.id} value={engine.id}>
                {engine.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">识别语言</label>
          <input
            type="text"
            placeholder="留空自动识别，例如 English"
            value={language}
            onChange={handleLanguageChange}
            disabled={disabled}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">输出格式</label>
          <div className="flex flex-wrap gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={outputFormats.srt}
                onChange={() => handleFormatToggle('srt')}
                className="w-4 h-4"
                disabled={disabled}
              />
              <span>SRT 字幕</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={outputFormats.txt}
                onChange={() => handleFormatToggle('txt')}
                className="w-4 h-4"
                disabled={disabled}
              />
              <span>纯文本</span>
            </label>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ParameterSettings
