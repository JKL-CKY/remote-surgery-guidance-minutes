import { useEffect, useRef, useCallback } from 'react'
import { useAppStore } from '../store/useAppStore'

interface UseWebSocketOptions {
  sessionId: string
  onMessage?: (message: any) => void
}

export const useWebSocket = ({ sessionId, onMessage }: UseWebSocketOptions) => {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectRef = useRef<NodeJS.Timeout | null>(null)
  const isConnectedRef = useRef(false)

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/${sessionId}`
    
    wsRef.current = new WebSocket(wsUrl)

    wsRef.current.onopen = () => {
      console.log('WebSocket connected')
      isConnectedRef.current = true
      useAppStore.getState().setIsStreaming(true)
    }

    wsRef.current.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        if (onMessage) {
          onMessage(message)
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error)
      isConnectedRef.current = false
    }

    wsRef.current.onclose = () => {
      console.log('WebSocket disconnected')
      isConnectedRef.current = false
      useAppStore.getState().setIsStreaming(false)
      
      if (reconnectRef.current) {
        clearTimeout(reconnectRef.current)
      }
      reconnectRef.current = setTimeout(() => {
        if (sessionId) {
          connect()
        }
      }, 3000)
    }
  }, [sessionId, onMessage])

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    if (reconnectRef.current) {
      clearTimeout(reconnectRef.current)
    }
    isConnectedRef.current = false
  }, [])

  const sendMessage = useCallback((type: string, data: Record<string, any>) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type, data, timestamp: Date.now() }))
    }
  }, [])

  const sendVideoFrame = useCallback((frameData: string) => {
    sendMessage('video_frame', { frame: frameData })
  }, [sendMessage])

  const sendAudioChunk = useCallback((audioData: ArrayBuffer) => {
    sendMessage('audio_chunk', { audio: audioData })
  }, [sendMessage])

  useEffect(() => {
    if (sessionId) {
      connect()
    }
    return () => {
      disconnect()
    }
  }, [sessionId, connect, disconnect])

  return {
    isConnected: isConnectedRef.current,
    sendMessage,
    sendVideoFrame,
    sendAudioChunk,
    connect,
    disconnect,
  }
}
