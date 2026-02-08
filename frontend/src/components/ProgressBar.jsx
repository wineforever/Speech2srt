import React from 'react'

const formatEta = (seconds) => {
  if (!Number.isFinite(seconds) || seconds < 0) {
    return ''
  }
  const total = Math.ceil(seconds)
  const mins = Math.floor(total / 60)
  const secs = total % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const ProgressBar = ({ progress, message, etaSeconds }) => {
  return (
    <div className="panel panel-subtle">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-lg font-display">处理进度</h3>
          <p className="text-xs text-slate-500 mt-1">后台队列实时刷新</p>
        </div>
        <span className="text-sm text-slate-600">{Math.round(progress)}%</span>
      </div>
      <div className="progress-track">
        <div className="progress-bar" style={{ width: `${progress}%` }}></div>
      </div>
      {etaSeconds !== null && (
        <p className="text-sm text-slate-600 mt-3">预计剩余：{formatEta(etaSeconds)}</p>
      )}
      {message && <p className="text-sm text-slate-600 mt-3">{message}</p>}
    </div>
  )
}

export default ProgressBar
