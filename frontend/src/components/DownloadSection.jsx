import React from 'react'

const DownloadSection = ({ outputFiles, onDownload }) => {
  if (!outputFiles) {
    return null
  }

  const { audio, srt, txt } = outputFiles

  return (
    <div className="panel">
      <span className="badge">Step 5</span>
      <h3 className="text-lg font-display mt-2">下载结果</h3>
      <div className="mt-4 space-y-3">
        {audio && (
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-4 rounded-xl bg-white/80 border border-slate-200">
            <div>
              <p className="font-medium">处理后的音频</p>
              <p className="text-sm text-slate-600">{audio}</p>
            </div>
            <button
              className="bg-secondary text-white px-4 py-2 rounded-full hover:opacity-90 transition"
              onClick={() => onDownload(audio)}
            >
              下载
            </button>
          </div>
        )}
        {srt && (
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-4 rounded-xl bg-white/80 border border-slate-200">
            <div>
              <p className="font-medium">SRT 字幕</p>
              <p className="text-sm text-slate-600">{srt}</p>
            </div>
            <button
              className="bg-secondary text-white px-4 py-2 rounded-full hover:opacity-90 transition"
              onClick={() => onDownload(srt)}
            >
              下载
            </button>
          </div>
        )}
        {txt && (
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-4 rounded-xl bg-white/80 border border-slate-200">
            <div>
              <p className="font-medium">纯文本</p>
              <p className="text-sm text-slate-600">{txt}</p>
            </div>
            <button
              className="bg-secondary text-white px-4 py-2 rounded-full hover:opacity-90 transition"
              onClick={() => onDownload(txt)}
            >
              下载
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default DownloadSection
