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

const createJob = ({ filename, cropSeconds, outputFormats, language }) => {
  return api.post('/process', {
    filename,
    crop_seconds: cropSeconds,
    output_formats: outputFormats,
    language
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

const healthCheck = () => api.get('/health')

export default {
  uploadFile,
  createJob,
  getJobStatus,
  downloadFile,
  previewAudio,
  healthCheck
}
