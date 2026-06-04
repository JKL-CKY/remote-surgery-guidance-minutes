import { create } from 'zustand'
import type { SurgerySession, TranscriptSegment, SurgerySummary, AudioAnalysis } from '../types'

interface AppState {
  currentSession: SurgerySession | null
  transcripts: TranscriptSegment[]
  summary: SurgerySummary | null
  audioAnalysis: AudioAnalysis | null
  isRecording: boolean
  isStreaming: boolean
  audioLevel: number
  setCurrentSession: (session: SurgerySession | null) => void
  addTranscript: (segment: TranscriptSegment) => void
  setTranscripts: (segments: TranscriptSegment[]) => void
  setSummary: (summary: SurgerySummary | null) => void
  setAudioAnalysis: (analysis: AudioAnalysis | null) => void
  setIsRecording: (recording: boolean) => void
  setIsStreaming: (streaming: boolean) => void
  setAudioLevel: (level: number) => void
  reset: () => void
}

export const useAppStore = create<AppState>((set) => ({
  currentSession: null,
  transcripts: [],
  summary: null,
  audioAnalysis: null,
  isRecording: false,
  isStreaming: false,
  audioLevel: 0,
  setCurrentSession: (session) => set({ currentSession: session }),
  addTranscript: (segment) =>
    set((state) => ({
      transcripts: [...state.transcripts, segment].sort((a, b) => a.start_time - b.start_time),
    })),
  setTranscripts: (segments) => set({ transcripts: segments }),
  setSummary: (summary) => set({ summary }),
  setAudioAnalysis: (analysis) => set({ audioAnalysis: analysis }),
  setIsRecording: (recording) => set({ isRecording: recording }),
  setIsStreaming: (streaming) => set({ isStreaming: streaming }),
  setAudioLevel: (level) => set({ audioLevel: level }),
  reset: () =>
    set({
      currentSession: null,
      transcripts: [],
      summary: null,
      audioAnalysis: null,
      isRecording: false,
      isStreaming: false,
      audioLevel: 0,
    }),
}))
