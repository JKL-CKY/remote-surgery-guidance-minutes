import React, { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Button, Tag, Space, Modal, message, Tabs, Badge, Card, Statistic, Row, Col } from 'antd'
import {
  VideoCameraOutlined,
  AudioOutlined,
  StopOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  FileTextOutlined,
  SendOutlined,
  ReloadOutlined,
  ArrowLeftOutlined,
  ExperimentOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { VideoPlayer } from '../components/VideoPlayer'
import { TranscriptView } from '../components/TranscriptView'
import { SummaryView } from '../components/SummaryView'
import { AudioMonitor } from '../components/AudioMonitor'
import { useAppStore } from '../store/useAppStore'
import { useWebSocket } from '../hooks/useWebSocket'
import { useMediaRecorder } from '../hooks/useMediaRecorder'
import { surgeryApi, transcriptApi, summaryApi, archiveApi, audioApi } from '../services/api'
import type { SurgerySession, TranscriptSegment, SurgerySummary, AudioAnalysis } from '../types'

export const SurgeryRoomPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const [session, setSession] = useState<SurgerySession | null>(null)
  const [loading, setLoading] = useState(true)
  const [elapsedTime, setElapsedTime] = useState(0)
  const [activeTab, setActiveTab] = useState('transcript')
  const [summary, setSummary] = useState<SurgerySummary | null>(null)
  const [audioAnalysis, setAudioAnalysis] = useState<AudioAnalysis | null>(null)
  const [generatingSummary, setGeneratingSummary] = useState(false)
  const [archiving, setArchiving] = useState(false)
  const timerRef = useRef<NodeJS.Timeout | null>(null)

  const {
    transcripts,
    isRecording,
    audioLevel,
    setTranscripts,
    addTranscript,
    setIsRecording,
    setAudioLevel,
    reset,
  } = useAppStore()

  const handleWebSocketMessage = useCallback((message: any) => {
    if (message.type === 'transcript' && message.data) {
      addTranscript(message.data as TranscriptSegment)
    } else if (message.type === 'status' && message.data) {
      if (message.data.audioLevel !== undefined) {
        setAudioLevel(message.data.audioLevel)
      }
    }
  }, [addTranscript, setAudioLevel])

  const { sendMessage, sendVideoFrame, sendAudioChunk } = useWebSocket({
    sessionId: sessionId || '',
    onMessage: handleWebSocketMessage,
  })

  const handleAudioChunk = useCallback((chunk: Blob) => {
    const reader = new FileReader()
    reader.onload = () => {
      const arrayBuffer = reader.result as ArrayBuffer
      sendAudioChunk(arrayBuffer)
    }
    reader.readAsArrayBuffer(chunk)
  }, [sendAudioChunk])

  const handleVideoFrame = useCallback((frame: string) => {
    sendVideoFrame(frame)
  }, [sendVideoFrame])

  const { startRecording, stopRecording } = useMediaRecorder({
    onAudioChunk: handleAudioChunk,
    onVideoFrame: session?.video_source ? undefined : handleVideoFrame,
  })

  useEffect(() => {
    if (!sessionId) return

    const loadSession = async () => {
      try {
        const [sessionData, transcriptsData, analysisData] = await Promise.all([
          surgeryApi.getSession(sessionId),
          transcriptApi.getTranscripts(sessionId).catch(() => []),
          audioApi.analyzeQuality(sessionId).catch(() => null),
        ])
        setSession(sessionData)
        setTranscripts(transcriptsData)
        setAudioAnalysis(analysisData)

        if (sessionData.status === 'active') {
          const startTime = dayjs(sessionData.start_time)
          setElapsedTime(dayjs().diff(startTime, 'second'))
          startTimer()
        }
      } catch (error) {
        message.error('加载手术会话失败')
        navigate('/')
      } finally {
        setLoading(false)
      }
    }

    loadSession()
  }, [sessionId, navigate, setTranscripts])

  const startTimer = () => {
    if (timerRef.current) clearInterval(timerRef.current)
    timerRef.current = setInterval(() => {
      setElapsedTime((prev) => prev + 1)
    }, 1000)
  }

  const stopTimer = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
  }

  const formatElapsedTime = (seconds: number) => {
    const hrs = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const handleStartRecording = async () => {
    try {
      await startRecording()
      setIsRecording(true)
      startTimer()
      message.success('开始录制')
    } catch (error) {
      message.error('无法访问麦克风/摄像头')
    }
  }

  const handleStopRecording = async () => {
    Modal.confirm({
      title: '确认结束录制',
      content: '结束后将生成手术摘要并可归档到手术记录系统。',
      onOk: async () => {
        stopRecording()
        stopTimer()
        setIsRecording(false)
        if (session) {
          await surgeryApi.endSession(session.session_id)
          message.success('录制已结束')
        }
      },
    })
  }

  const handleGenerateSummary = async () => {
    if (!session) return
    setGeneratingSummary(true)
    try {
      const result = await summaryApi.generateSummary(session.session_id)
      setSummary(result)
      setActiveTab('summary')
      message.success('手术摘要生成成功')
    } catch (error) {
      message.error('生成摘要失败')
    } finally {
      setGeneratingSummary(false)
    }
  }

  const handleArchive = async () => {
    if (!session) return
    setArchiving(true)
    try {
      await archiveApi.sendToArchive(session.session_id)
      message.success('手术记录已归档到邮件系统')
    } catch (error) {
      message.error('归档失败')
    } finally {
      setArchiving(false)
    }
  }

  const handleRefreshTranscripts = async () => {
    if (!session) return
    try {
      const data = await transcriptApi.getTranscripts(session.session_id)
      setTranscripts(data)
      message.success(`已加载 ${data.length} 条转写记录`)
    } catch (error) {
      message.error('刷新失败')
    }
  }

  const handleRefreshAnalysis = async () => {
    if (!session) return
    try {
      const data = await audioApi.analyzeQuality(session.session_id)
      setAudioAnalysis(data)
    } catch (error) {
      // ignore
    }
  }

  useEffect(() => {
    const interval = setInterval(() => {
      if (isRecording && sessionId) {
        handleRefreshAnalysis()
      }
    }, 10000)
    return () => clearInterval(interval)
  }, [isRecording, sessionId])

  useEffect(() => {
    return () => {
      stopTimer()
      reset()
    }
  }, [reset])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">加载手术会话中...</p>
        </div>
      </div>
    )
  }

  if (!session) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <p className="text-gray-600">手术会话不存在</p>
      </div>
    )
  }

  const isSessionActive = session.status === 'active'

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4 sticky top-0 z-50 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate('/')}
              className="mr-2"
            />
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold text-gray-800">{session.surgery_type}</h1>
                <Badge
                  status={isSessionActive ? 'processing' : 'default'}
                  text={isSessionActive ? '进行中' : '已结束'}
                />
                {isRecording && (
                  <Tag color="red" icon={<AudioOutlined />}>
                    录制中
                  </Tag>
                )}
              </div>
              <div className="text-sm text-gray-500 flex items-center gap-4 mt-1">
                <span>患者: {session.patient_name} (ID: {session.patient_id})</span>
                <span>主刀: {session.primary_surgeon}</span>
                <span>远程专家: {session.remote_expert}</span>
                <span>手术室: {session.operating_room}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-2xl font-mono font-bold text-gray-800">
                {formatElapsedTime(elapsedTime)}
              </div>
              <div className="text-xs text-gray-500">手术时长</div>
            </div>

            <Space>
              {isSessionActive && !isRecording && (
                <Button
                  type="primary"
                  size="large"
                  icon={<PlayCircleOutlined />}
                  onClick={handleStartRecording}
                  className="bg-green-500 hover:bg-green-600"
                >
                  开始录制
                </Button>
              )}
              {isSessionActive && isRecording && (
                <Button
                  type="primary"
                  size="large"
                  danger
                  icon={<StopOutlined />}
                  onClick={handleStopRecording}
                >
                  结束录制
                </Button>
              )}
              {!isSessionActive && transcripts.length > 0 && !summary && (
                <Button
                  type="primary"
                  size="large"
                  icon={<FileTextOutlined />}
                  loading={generatingSummary}
                  onClick={handleGenerateSummary}
                >
                  生成摘要
                </Button>
              )}
              {summary && (
                <Button
                  type="primary"
                  size="large"
                  icon={<SendOutlined />}
                  loading={archiving}
                  onClick={handleArchive}
                  className="bg-purple-500 hover:bg-purple-600"
                >
                  归档到邮件
                </Button>
              )}
            </Space>
          </div>
        </div>
      </header>

      <main className="p-6">
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-8">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden mb-6">
              <div className="aspect-video bg-gray-900">
                {session.video_source ? (
                  <VideoPlayer
                    src={session.video_source}
                    isLive={isSessionActive}
                    className="w-full h-full"
                  />
                ) : (
                  <div className="w-full h-full flex flex-col items-center justify-center text-gray-500">
                    <VideoCameraOutlined className="text-6xl mb-4 opacity-50" />
                    <p className="text-lg">等待腔镜视频信号...</p>
                    <p className="text-sm mt-2">请连接手术腔镜视频源或开启摄像头</p>
                  </div>
                )}
              </div>
            </div>

            <Card className="shadow-sm border border-gray-200">
              <Tabs
                activeKey={activeTab}
                onChange={setActiveTab}
                items={[
                  {
                    key: 'transcript',
                    label: (
                      <span className="flex items-center gap-2">
                        <FileTextOutlined />
                        实时转写
                        <Badge count={transcripts.length} size="small" />
                      </span>
                    ),
                    children: (
                      <div>
                        <div className="flex justify-between items-center mb-4">
                          <span className="text-sm text-gray-500">
                            共 {transcripts.length} 条转写记录
                          </span>
                          <Button
                            size="small"
                            icon={<ReloadOutlined />}
                            onClick={handleRefreshTranscripts}
                          >
                            刷新
                          </Button>
                        </div>
                        <TranscriptView transcripts={transcripts} />
                      </div>
                    ),
                  },
                  {
                    key: 'summary',
                    label: (
                      <span className="flex items-center gap-2">
                        <ExperimentOutlined />
                        手术摘要
                      </span>
                    ),
                    children: summary ? (
                      <SummaryView summary={summary} />
                    ) : (
                      <div className="text-center py-12 text-gray-500">
                        <FileTextOutlined className="text-5xl mb-4 opacity-30" />
                        <p className="text-lg">暂无手术摘要</p>
                        <p className="text-sm mt-2">
                          {isSessionActive
                            ? '请先结束录制，然后生成手术摘要'
                            : '点击右上角"生成摘要"按钮'}
                        </p>
                      </div>
                    ),
                  },
                ]}
              />
            </Card>
          </div>

          <div className="col-span-4 space-y-6">
            <AudioMonitor
              audioLevel={audioLevel}
              analysis={audioAnalysis}
              isRecording={isRecording}
            />

            <Card className="shadow-sm border border-gray-200">
              <h3 className="text-sm font-semibold text-gray-700 mb-4">手术信息</h3>
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <Statistic
                    title="手术类型"
                    value={session.surgery_type}
                    valueStyle={{ fontSize: '14px' }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="状态"
                    value={isSessionActive ? '进行中' : '已结束'}
                    valueStyle={{ fontSize: '14px', color: isSessionActive ? '#52c41a' : '#8c8c8c' }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="主刀医生"
                    value={session.primary_surgeon}
                    valueStyle={{ fontSize: '14px' }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="远程专家"
                    value={session.remote_expert}
                    valueStyle={{ fontSize: '14px' }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="手术室"
                    value={session.operating_room}
                    valueStyle={{ fontSize: '14px' }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="会话ID"
                    value={session.session_id}
                    valueStyle={{ fontSize: '12px' }}
                  />
                </Col>
              </Row>
            </Card>

            <Card className="shadow-sm border border-gray-200">
              <h3 className="text-sm font-semibold text-gray-700 mb-4">快捷操作</h3>
              <Space direction="vertical" className="w-full">
                <Button block icon={<ReloadOutlined />} onClick={handleRefreshTranscripts}>
                  刷新转写记录
                </Button>
                <Button block icon={<PauseCircleOutlined />} disabled={!isRecording}>
                  暂停录制
                </Button>
                <Button
                  block
                  icon={<FileTextOutlined />}
                  disabled={!summary}
                  onClick={() => setActiveTab('summary')}
                >
                  查看手术摘要
                </Button>
              </Space>
            </Card>
          </div>
        </div>
      </main>
    </div>
  )
}
