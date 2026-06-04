export interface SurgerySession {
  id: number
  session_id: string
  patient_id: string
  patient_name: string
  surgery_type: string
  primary_surgeon: string
  remote_expert: string
  operating_room: string
  status: 'active' | 'completed' | 'paused'
  start_time: string
  end_time?: string
  video_source?: string
  audio_source?: string
}

export interface TranscriptSegment {
  speaker: string
  speaker_role: string
  start_time: number
  end_time: number
  text: string
  confidence: number
  is_anatomical_term: boolean
  anatomical_terms?: string[]
  is_surgery_step: boolean
  surgery_step?: string
}

export interface AudioSegment {
  id: number
  session_id: number
  segment_index: number
  file_path: string
  start_time: number
  end_time: number
  duration: number
  has_electric_scalpel: boolean
  has_monitor_alarm: boolean
  noise_reduction_applied: boolean
  processed: boolean
}

export interface SurgerySummary {
  key_points: string[]
  surgical_steps: Array<{
    time: number
    step: string
    description: string
  }>
  anatomical_landmarks: string[]
  technical_improvements: string[]
  complications: string[]
  overall_assessment: string
}

export interface AudioAnalysis {
  total_segments: number
  processed_segments: number
  electric_scalpel_detected: number
  monitor_alarm_detected: number
  noise_reduction_applied_rate: number
}

export interface WebSocketMessage {
  type: 'video_frame' | 'audio_chunk' | 'transcript' | 'control' | 'status'
  data: Record<string, any>
  timestamp: number
}
