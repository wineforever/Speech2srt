import React, { useEffect, useRef, useState } from 'react'

const AudioPlayer = ({ audioUrl, filename, disabled }) => {
  const audioRef = useRef(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) {
      return undefined
    }

    const handleLoadedMetadata = () => {
      setDuration(audio.duration || 0)
      setIsLoading(false)
    }

    const handleTimeUpdate = () => {
      setCurrentTime(audio.currentTime)
    }

    const handleEnded = () => {
      setIsPlaying(false)
      setCurrentTime(0)
    }

    audio.addEventListener('loadedmetadata', handleLoadedMetadata)
    audio.addEventListener('timeupdate', handleTimeUpdate)
    audio.addEventListener('ended', handleEnded)

    return () => {
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata)
      audio.removeEventListener('timeupdate', handleTimeUpdate)
      audio.removeEventListener('ended', handleEnded)
    }
  }, [audioUrl])

  useEffect(() => {
    setIsPlaying(false)
    setCurrentTime(0)
    setIsLoading(true)
  }, [audioUrl])

  const handlePlayPause = () => {
    if (disabled || !audioRef.current || isLoading) {
      return
    }

    if (isPlaying) {
      audioRef.current.pause()
    } else {
      audioRef.current.play()
    }
    setIsPlaying(!isPlaying)
  }

  const handleTimeChange = (event) => {
    if (disabled || !audioRef.current || isLoading) {
      return
    }
    const newTime = parseFloat(event.target.value)
    audioRef.current.currentTime = newTime
    setCurrentTime(newTime)
  }

  const formatTime = (timeInSeconds) => {
    const minutes = Math.floor(timeInSeconds / 60)
    const seconds = Math.floor(timeInSeconds % 60)
    return `${minutes}:${seconds.toString().padStart(2, '0')}`
  }

  if (!audioUrl) {
    return null
  }

  return (
    <div className="panel panel-subtle">
      <div className="flex items-center justify-between mb-4">
        <div>
          <span className="badge">Step 2</span>
          <h3 className="text-lg font-display mt-2">音频预览</h3>
        </div>
        <span className="text-sm text-slate-600">{filename}</span>
      </div>
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-4">
          <button
            className="bg-primary text-white p-3 rounded-full hover:opacity-90 transition"
            onClick={handlePlayPause}
            disabled={disabled || isLoading}
          >
            {isPlaying ? (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            )}
          </button>
          <div className="flex-1">
            <input
              type="range"
              min="0"
              max={duration || 0}
              value={currentTime}
              onChange={handleTimeChange}
              className="w-full"
              disabled={disabled || isLoading}
            />
          </div>
          <div className="text-sm text-slate-600 min-w-[110px] text-right">
            {formatTime(currentTime)} / {isLoading ? '--:--' : formatTime(duration)}
          </div>
        </div>
        <audio ref={audioRef} src={audioUrl} className="hidden" />
      </div>
    </div>
  )
}

export default AudioPlayer
