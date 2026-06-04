import React from 'react'
import type { SurgerySummary } from '../types'

interface SummaryViewProps {
  summary: SurgerySummary
  className?: string
}

export const SummaryView: React.FC<SummaryViewProps> = ({ summary, className = '' }) => {
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className={`space-y-6 ${className}`}>
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl p-6 text-white">
        <h3 className="text-xl font-bold mb-2">📊 总体评估</h3>
        <p className="leading-relaxed opacity-95">{summary.overall_assessment}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <span className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">🔑</span>
            手术要点
          </h3>
          <ul className="space-y-2">
            {summary.key_points.map((point, index) => (
              <li key={index} className="flex items-start gap-2 text-gray-700">
                <span className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">
                  {index + 1}
                </span>
                <span>{point}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <span className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">💡</span>
            技术改进建议
          </h3>
          <ul className="space-y-2">
            {summary.technical_improvements.map((imp, index) => (
              <li key={index} className="flex items-start gap-2 text-gray-700">
                <span className="text-green-500 mt-0.5">✓</span>
                <span>{imp}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <span className="w-8 h-8 bg-yellow-100 rounded-lg flex items-center justify-center">🏗️</span>
            解剖标识
          </h3>
          <div className="flex flex-wrap gap-2">
            {summary.anatomical_landmarks.map((term, index) => (
              <span
                key={index}
                className="px-3 py-1 bg-yellow-50 text-yellow-800 rounded-full text-sm border border-yellow-200"
              >
                📍 {term}
              </span>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <span className="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center">⚠️</span>
            并发症风险
          </h3>
          <ul className="space-y-2">
            {summary.complications.map((comp, index) => (
              <li key={index} className="flex items-start gap-2 text-gray-700">
                <span className="text-red-500 mt-0.5">!</span>
                <span>{comp}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
          <span className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">📝</span>
          手术步骤时间线
        </h3>
        <div className="relative">
          <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-purple-200" />
          <div className="space-y-4">
            {summary.surgical_steps.map((step, index) => (
              <div key={index} className="relative pl-12">
                <div className="absolute left-0 top-1 w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center text-white text-sm font-bold">
                  {index + 1}
                </div>
                <div className="bg-purple-50 rounded-lg p-4 border border-purple-100">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-purple-700">{step.step}</span>
                    <span className="text-sm text-purple-500 font-mono">{formatTime(step.time)}</span>
                  </div>
                  <p className="text-gray-700">{step.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
