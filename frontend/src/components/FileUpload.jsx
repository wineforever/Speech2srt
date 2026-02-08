import React, { useRef, useState } from 'react'

const FileUpload = ({ onFileUpload, disabled }) => {
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState('')
  const fileInputRef = useRef(null)

  const triggerFileDialog = () => {
    if (!disabled) {
      fileInputRef.current?.click()
    }
  }

  const handleDragOver = (event) => {
    event.preventDefault()
    if (!disabled) {
      setIsDragging(true)
    }
  }

  const handleDragLeave = (event) => {
    event.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (event) => {
    event.preventDefault()
    setIsDragging(false)
    if (disabled) {
      return
    }

    const files = event.dataTransfer.files
    if (files.length > 0) {
      handleFileSelect(files[0])
    }
  }

  const handleFileSelect = (file) => {
    const validFormats = ['wav', 'mp3']
    const fileExtension = file.name.split('.').pop().toLowerCase()

    if (!validFormats.includes(fileExtension)) {
      setError('仅支持 WAV 或 MP3 格式')
      return
    }

    if (file.size > 100 * 1024 * 1024) {
      setError('文件大小不能超过 100MB')
      return
    }

    setError('')
    onFileUpload(file)
  }

  const handleFileInputChange = (event) => {
    const files = event.target.files
    if (files.length > 0) {
      handleFileSelect(files[0])
    }
    event.target.value = ''
  }

  return (
    <div
      className={`upload-area panel ${isDragging ? 'active' : ''} ${disabled ? 'opacity-60 cursor-not-allowed' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={triggerFileDialog}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault()
          triggerFileDialog()
        }
      }}
      role="button"
      tabIndex={disabled ? -1 : 0}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".wav,.mp3"
        onChange={handleFileInputChange}
        className="hidden"
        disabled={disabled}
      />
      <div className="flex flex-col items-center text-center gap-3">
        <span className="badge">Step 1</span>
        <h3 className="text-xl font-display">上传音频</h3>
        <p className="text-sm text-slate-600">拖拽文件或点击选择，支持 WAV / MP3</p>
        {error && <p className="text-sm text-danger">{error}</p>}
        <button
          className="bg-primary text-white px-6 py-2 rounded-full hover:opacity-90 transition"
          onClick={(event) => {
            event.stopPropagation()
            triggerFileDialog()
          }}
          disabled={disabled}
        >
          选择文件
        </button>
      </div>
    </div>
  )
}

export default FileUpload
