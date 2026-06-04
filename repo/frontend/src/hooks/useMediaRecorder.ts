import { useEffect, useRef, useCallback, useState } from 'react'

interface UseMediaRecorderOptions {
  onAudioChunk?: (chunk: Blob) => void
  onVideoFrame?: (frame: string) => void
  audioConstraints?: MediaStreamConstraints['audio']
  videoConstraints?: MediaStreamConstraints['video']
}

export const useMediaRecorder = ({
  onAudioChunk, onVideoFrame, audioConstraints = true, videoConstraints }: UseMediaRecorderOptions) => {
  const [isRecording, setIsRecording] = useState(false)
  const [stream, setStream] = useState<MediaStream | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const videoElementRef = useRef<HTMLVideoElement | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const frameIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const audioLevelIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const [audioLevel, setAudioLevel] = useState(0)

  const startRecording = useCallback(async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: audioConstraints,
        video: videoConstraints || false,
      })
      setStream(mediaStream)

      if (mediaStream.getAudioTracks().length > 0) {
        const audioTrack = mediaStream.getAudioTracks()[0]
        const audioStream = new MediaStream([audioTrack])
        
        mediaRecorderRef.current = new MediaRecorder(audioStream, {
          mimeType: MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : undefined,
        })

        mediaRecorderRef.current.ondataavailable = (event) => {
          if (event.data.size > 0 && onAudioChunk) {
            onAudioChunk(event.data)
          }
        }

        mediaRecorderRef.current.start(1000)

        audioContextRef.current = new AudioContext()
        analyserRef.current = audioContextRef.current.createAnalyser()
        const source = audioContextRef.current.createMediaStreamSource(audioStream)
        source.connect(analyserRef.current)
        analyserRef.current.fftSize = 256

        const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount)
        
        audioLevelIntervalRef.current = setInterval(() => {
          if (analyserRef.current) {
            analyserRef.current.getByteFrequencyData(dataArray)
            const average = dataArray.reduce((a, b) => a + b) / dataArray.length
            setAudioLevel(average / 255)
          }
        }, 100)
      }

      if (mediaStream.getVideoTracks().length > 0 && onVideoFrame) {
        if (!canvasRef.current) {
          canvasRef.current = document.createElement('canvas')
        }
        const canvas = canvasRef.current
        const ctx = canvas.getContext('2d')
        
        if (!videoElementRef.current) {
          videoElementRef.current = document.createElement('video')
          videoElementRef.current.muted = true
          videoElementRef.current.srcObject = mediaStream
          videoElementRef.current.play()
        }
        
        frameIntervalRef.current = setInterval(() => {
          if (videoElementRef.current && canvas && ctx) {
            canvas.width = videoElementRef.current.videoWidth || 640
            canvas.height = videoElementRef.current.videoHeight || 480
            ctx.drawImage(videoElementRef.current, 0, 0)
            const frameData = canvas.toDataURL('image/jpeg', 0.6)
            onVideoFrame(frameData)
          }
        }, 100)
      }

      setIsRecording(true)
    } catch (error) {
      console.error('Failed to start recording:', error)
    }
  }, [audioConstraints, videoConstraints, onAudioChunk, onVideoFrame])

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop()
      mediaRecorderRef.current = null
    }
    
    if (stream) {
      stream.getTracks().forEach((track) => track.stop())
      setStream(null)
    }

    if (frameIntervalRef.current) {
      clearInterval(frameIntervalRef.current)
      frameIntervalRef.current = null
    }

    if (audioLevelIntervalRef.current) {
      clearInterval(audioLevelIntervalRef.current)
      audioLevelIntervalRef.current = null
    }

    if (audioContextRef.current) {
      audioContextRef.current.close()
      audioContextRef.current = null
    }

    setIsRecording(false)
    setAudioLevel(0)
  }, [stream])

  useEffect(() => {
    return () => {
      stopRecording()
    }
  }, [stopRecording])

  return {
    isRecording,
    stream,
    audioLevel,
    startRecording,
    stopRecording,
  }
}
