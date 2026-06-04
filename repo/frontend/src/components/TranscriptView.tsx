import React, { useRef, useEffect } from 'react'
import type { TranscriptSegment } from '../types'

interface TranscriptViewProps {
  transcripts: TranscriptSegment[]
  onSegmentClick?: (segment: TranscriptSegment) => void
  highlightTime?: number
}

export const TranscriptView: React.FC<TranscriptViewProps> = ({
  transcripts,
  onSegmentClick,
  highlightTime,
}) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const activeRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (activeRef.current && containerRef.current) {
      activeRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, [transcripts.length, highlightTime])

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const getSpeakerColor = (speaker: string) => {
    const colors: Record<string, string> = {
      'SPEAKER_00': 'bg-blue-100 border-blue-300 text-blue-900',
      'SPEAKER_01': 'bg-green-100 border-green-300 text-green-900',
      '未知': 'bg-gray-100 border-gray-300 text-gray-900',
    }
    return colors[speaker] || 'bg-purple-100 border-purple-300 text-purple-900'
  }

  const getRoleBadge = (role: string) => {
    if (role === '主刀医生') {
      return <span className="text-xs font-medium bg-red-100 text-red-700 px-2 py-0.5 rounded">主刀</span>
    }
    if (role === '远程专家') {
      return <span className="text-xs font-medium bg-blue-100 text-blue-700 px-2 py-0.5 rounded">专家</span>
    }
    return null
  }

  const isActive = (segment: TranscriptSegment) => {
    if (highlightTime === undefined) return false
    return highlightTime >= segment.start_time && highlightTime <= segment.end_time
  }

  if (transcripts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-400">
        <svg className="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
        </svg>
        <p className="text-lg">暂无语音转写</p>
        <p className="text-sm">开始录制后，语音内容将实时显示在这里</p>
      </div>
    )
  }

  return (
    <div ref={containerRef} className="space-y-3 max-h-96 overflow-y-auto p-4">
      {transcripts.map((segment, index) => (
        <div
          key={index}
          ref={isActive(segment) ? activeRef : undefined}
          onClick={() => onSegmentClick?.(segment)}
          className={`p-4 rounded-lg border-l-4 cursor-pointer transition-all ${getSpeakerColor(segment.speaker)} ${
            isActive(segment) ? 'ring-2 ring-blue-400 scale-[1.02]' : 'hover:shadow-md'
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="font-mono text-sm font-bold">{formatTime(segment.start_time)}</span>
              <span className="font-medium">{segment.speaker}</span>
              {getRoleBadge(segment.speaker_role)}
            </div>
            <div className="flex items-center gap-1">
              {segment.is_surgery_step && (
                <span className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded">步骤</span>
              )}
              {segment.is_anatomical_term && (
                <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded">解剖</span>
              )}
            </div>
          </div>
          <p className="text-sm leading-relaxed">{segment.text}</p>
          {segment.anatomical_terms && segment.anatomical_terms.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {segment.anatomical_terms.map((term, i) => (
                <span key={i} className="text-xs bg-yellow-50 text-yellow-800 px-2 py-0.5 rounded">
                  📍 {term}
                </span>
              ))}
            </div>
          )}
          {segment.surgery_step && (
            <div className="mt-2">
              <span className="text-xs bg-orange-50 text-orange-800 px-2 py-0.5 rounded font-medium">
                🔧 {segment.surgery_step}
              </span>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
