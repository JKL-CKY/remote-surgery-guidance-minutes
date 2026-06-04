import axios from 'axios'
import type { SurgerySession, TranscriptSegment, SurgerySummary, AudioAnalysis } from '../types'

const api = axios.create({
  baseURL: '/api',
  timeout: 300000,
})

export const surgeryApi = {
  createSession: (data: Omit<SurgerySession, 'id' | 'session_id' | 'status' | 'start_time'>) =>
    api.post<SurgerySession>('/surgery', data).then((res) => res.data),

  listSessions: (params?: { status?: string; skip?: number; limit?: number }) =>
    api.get<SurgerySession[]>('/surgery', { params }).then((res) => res.data),

  getSession: (sessionId: string) =>
    api.get<SurgerySession>(`/surgery/${sessionId}`).then((res) => res.data),

  endSession: (sessionId: string) =>
    api.put<SurgerySession>(`/surgery/${sessionId}/end`).then((res) => res.data),

  deleteSession: (sessionId: string) =>
    api.delete(`/surgery/${sessionId}`).then((res) => res.data),
}

export const audioApi = {
  uploadAudio: (sessionId: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/audio/upload/${sessionId}`, formData).then((res) => res.data)
  },

  processAudio: (sessionId: string, segmentIndex: number, filePath: string) =>
    api.post(`/audio/process/${sessionId}`, { segment_index: segmentIndex, file_path: filePath }).then((res) => res.data),

  processBatch: (sessionId: string) =>
    api.post(`/audio/process-batch/${sessionId}`).then((res) => res.data),

  getSegments: (sessionId: string) =>
    api.get(`/audio/segments/${sessionId}`).then((res) => res.data),

  analyzeQuality: (sessionId: string) =>
    api.get<AudioAnalysis>(`/audio/analyze/${sessionId}`).then((res) => res.data),
}

export const transcriptApi = {
  transcribeSegment: (sessionId: string, audioFilePath: string) =>
    api.post<TranscriptSegment[]>(`/transcript/transcribe-segment/${sessionId}`, { audio_file_path: audioFilePath }).then((res) => res.data),

  getTranscripts: (sessionId: string) =>
    api.get<TranscriptSegment[]>(`/transcript/${sessionId}`).then((res) => res.data),

  getSurgerySteps: (sessionId: string) =>
    api.get(`/transcript/surgery-steps/${sessionId}`).then((res) => res.data),

  getAnatomicalTerms: (sessionId: string) =>
    api.get(`/transcript/anatomical-terms/${sessionId}`).then((res) => res.data),
}

export const summaryApi = {
  generateSummary: (sessionId: string) =>
    api.post<SurgerySummary>(`/summary/generate/${sessionId}`).then((res) => res.data),

  getSummary: (sessionId: string) =>
    api.get<SurgerySummary>(`/summary/${sessionId}`).then((res) => res.data),

  regenerateSummary: (sessionId: string) =>
    api.post<SurgerySummary>(`/summary/regenerate/${sessionId}`).then((res) => res.data),
}

export const archiveApi = {
  sendToArchive: (sessionId: string, recipientEmail?: string) =>
    api.post(`/archive/send/${sessionId}`, null, { params: { recipient_email: recipientEmail } }).then((res) => res.data),

  getArchiveStatus: (sessionId: string) =>
    api.get(`/archive/status/${sessionId}`).then((res) => res.data),
}

export default api
