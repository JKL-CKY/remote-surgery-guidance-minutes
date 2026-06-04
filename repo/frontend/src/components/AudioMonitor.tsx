import React from 'react'
import type { AudioAnalysis } from '../types'

interface AudioMonitorProps {
  audioLevel: number
  analysis?: AudioAnalysis | null
  isRecording: boolean
}

export const AudioMonitor: React.FC<AudioMonitorProps> = ({ audioLevel, analysis, isRecording }) => {
  const bars = 20
  const activeBars = Math.floor(audioLevel * bars)

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
        <span className={`w-2 h-2 rounded-full ${isRecording ? 'bg-red-500 animate-pulse' : 'bg-gray-400'}`} />
        音频监控
      </h3>
      
      <div className="flex items-end gap-1 h-16 mb-4">
        {Array.from({ length: bars }).map((_, i) => (
          <div
            key={i}
            className={`flex-1 rounded-t transition-all duration-75 ${
              i < activeBars
                ? i < bars * 0.6
                  ? 'bg-green-400'
                  : i < bars * 0.85
                  ? 'bg-yellow-400'
                  : 'bg-red-400'
                : 'bg-gray-200'
            }`}
            style={{
              height: `${i < activeBars ? ((i + 1) / bars) * 100 : 10}%`,
            }}
          />
        ))}
      </div>

      {analysis && (
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-gray-500 text-xs">音频片段总数</p>
            <p className="text-lg font-bold text-gray-800">{analysis.total_segments}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-gray-500 text-xs">已处理片段</p>
            <p className="text-lg font-bold text-blue-600">{analysis.processed_segments}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-gray-500 text-xs">电刀干扰检测</p>
            <p className={`text-lg font-bold ${analysis.electric_scalpel_detected > 0 ? 'text-orange-600' : 'text-green-600'}`}>
              {analysis.electric_scalpel_detected} 次
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-gray-500 text-xs">监护仪警报检测</p>
            <p className={`text-lg font-bold ${analysis.monitor_alarm_detected > 0 ? 'text-red-600' : 'text-green-600'}`}>
              {analysis.monitor_alarm_detected} 次
            </p>
          </div>
        </div>
      )}

      <div className="mt-3 pt-3 border-t border-gray-100">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>降噪处理率</span>
          <span className="font-medium">{analysis ? `${Math.round(analysis.noise_reduction_applied_rate * 100)}%` : '0%'}</span>
        </div>
        <div className="mt-1 h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-400 to-green-400 transition-all"
            style={{ width: `${analysis ? analysis.noise_reduction_applied_rate * 100 : 0}%` }}
          />
        </div>
      </div>
    </div>
  )
}
