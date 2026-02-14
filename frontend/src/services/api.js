import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json'
  }
})

const uploadFile = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

const createJob = ({ filename, originalFilename, cropSeconds, outputFormats, language, asrEngine }) => {
  return api.post('/process', {
    filename,
    original_filename: originalFilename,
    crop_seconds: cropSeconds,
    output_formats: outputFormats,
    language,
    asr_engine: asrEngine
  })
}

const getJobStatus = (jobId) => {
  return api.get(`/status/${jobId}`)
}

const downloadFile = (filename) => {
  return api.get(`/download/${filename}`, {
    responseType: 'blob'
  })
}

const previewAudio = (filename) => `${api.defaults.baseURL}/preview/${filename}`
const completionSoundUrl = () => `${api.defaults.baseURL}/assets/completion-sound`

const healthCheck = () => api.get('/health')
const getAsrEngines = () => api.get('/asr-engines')

export default {
  uploadFile,
  createJob,
  getJobStatus,
  downloadFile,
  previewAudio,
  completionSoundUrl,
  healthCheck,
  getAsrEngines
}
