import os
import numpy as np
from typing import List, Dict, Any, Optional
from ..core.config import settings


class SpeakerDiarization:
    def __init__(self):
        self.auth_token = settings.PYANNOTE_AUTH_TOKEN
        self.diarization_model_name = settings.PYANNOTE_SPEAKER_DIARIZATION_MODEL
        self.pipeline = None
        self._model_loaded = False

    def load_model(self):
        if self._model_loaded:
            return
        
        try:
            from pyannote.audio import Pipeline
            
            if self.auth_token:
                self.pipeline = Pipeline.from_pretrained(
                    self.diarization_model_name,
                    use_auth_token=self.auth_token
                )
            else:
                self.pipeline = None
                print("Warning: PyAnnote auth token not provided. Using fallback diarization.")
            
            self._model_loaded = True
        except Exception as e:
            print(f"Failed to load pyannote model: {e}")
            self.pipeline = None
            self._model_loaded = True

    def diarize(self, audio_path: str, num_speakers: Optional[int] = 2) -> List[Dict[str, Any]]:
        self.load_model()
        
        if self.pipeline is not None and os.path.exists(audio_path):
            try:
                return self._diarize_with_pyannote(audio_path, num_speakers)
            except Exception as e:
                print(f"PyAnnote diarization failed: {e}. Using fallback.")
        
        return self._fallback_diarization(audio_path, num_speakers)

    def _diarize_with_pyannote(self, audio_path: str, 
                               num_speakers: Optional[int]) -> List[Dict[str, Any]]:
        diarization = self.pipeline(
            audio_path,
            num_speakers=num_speakers
        )
        
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append({
                "speaker": speaker,
                "start_time": float(turn.start),
                "end_time": float(turn.end),
                "duration": float(turn.end - turn.start)
            })
        
        return segments

    def _fallback_diarization(self, audio_path: str, 
                              num_speakers: Optional[int] = 2) -> List[Dict[str, Any]]:
        import librosa
        
        if not os.path.exists(audio_path):
            return []
        
        try:
            y, sr = librosa.load(audio_path, sr=16000, mono=True)
        except Exception as e:
            print(f"Failed to load audio for fallback diarization: {e}")
            return []
        
        duration = len(y) / sr
        segments = []
        
        num_speakers = num_speakers or 2
        segment_duration = 30.0
        
        for start_time in np.arange(0, duration, segment_duration):
            end_time = min(start_time + segment_duration, duration)
            
            segment = y[int(start_time * sr):int(end_time * sr)]
            
            if len(segment) == 0:
                continue
            
            rms = np.sqrt(np.mean(segment ** 2))
            
            if rms > 0.01:
                speaker_idx = int((start_time // 60) % num_speakers)
                speaker = f"SPEAKER_{speaker_idx:02d}"
                
                segments.append({
                    "speaker": speaker,
                    "start_time": float(start_time),
                    "end_time": float(end_time),
                    "duration": float(end_time - start_time)
                })
        
        if len(segments) == 0 and duration > 0:
            mid_point = duration / 2
            segments = [
                {
                    "speaker": "SPEAKER_00",
                    "start_time": 0.0,
                    "end_time": float(mid_point),
                    "duration": float(mid_point)
                },
                {
                    "speaker": "SPEAKER_01",
                    "start_time": float(mid_point),
                    "end_time": float(duration),
                    "duration": float(duration - mid_point)
                }
            ]
        
        return segments

    def assign_speaker_roles(self, segments: List[Dict[str, Any]], 
                             speaker_mapping: Dict[str, str] = None) -> List[Dict[str, Any]]:
        if speaker_mapping is None:
            speaker_mapping = {
                "SPEAKER_00": "主刀医生",
                "SPEAKER_01": "远程专家"
            }
        
        for seg in segments:
            speaker = seg.get("speaker", "未知")
            seg["role"] = speaker_mapping.get(speaker, "其他")
        
        return segments

    def get_speaker_statistics(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        speaker_stats = {}
        
        for seg in segments:
            speaker = seg.get("speaker", "未知")
            duration = seg.get("duration", 0)
            
            if speaker not in speaker_stats:
                speaker_stats[speaker] = {
                    "total_duration": 0.0,
                    "segment_count": 0,
                    "avg_segment_duration": 0.0
                }
            
            speaker_stats[speaker]["total_duration"] += duration
            speaker_stats[speaker]["segment_count"] += 1
        
        for speaker, stats in speaker_stats.items():
            if stats["segment_count"] > 0:
                stats["avg_segment_duration"] = (
                    stats["total_duration"] / stats["segment_count"]
                )
        
        return speaker_stats

    def merge_short_segments(self, segments: List[Dict[str, Any]], 
                             min_duration: float = 1.0) -> List[Dict[str, Any]]:
        if not segments:
            return []
        
        merged = []
        current = segments[0]
        
        for seg in segments[1:]:
            if (seg.get("speaker") == current.get("speaker") and
                seg.get("start_time", 0) - current.get("end_time", 0) < 0.5):
                current["end_time"] = seg["end_time"]
                current["duration"] = current["end_time"] - current["start_time"]
            else:
                if current.get("duration", 0) >= min_duration:
                    merged.append(current)
                current = seg.copy()
        
        if current.get("duration", 0) >= min_duration:
            merged.append(current)
        
        return merged

    def smooth_diarization(self, segments: List[Dict[str, Any]], 
                           window_size: float = 5.0) -> List[Dict[str, Any]]:
        if len(segments) < 3:
            return segments
        
        smoothed = []
        i = 0
        
        while i < len(segments):
            current = segments[i]
            window_end = current["start_time"] + window_size
            
            window_segments = [current]
            j = i + 1
            
            while j < len(segments) and segments[j]["start_time"] < window_end:
                window_segments.append(segments[j])
                j += 1
            
            if len(window_segments) >= 3:
                speakers = [s["speaker"] for s in window_segments]
                dominant_speaker = max(set(speakers), key=speakers.count)
                
                if current["speaker"] != dominant_speaker:
                    current["speaker"] = dominant_speaker
            
            smoothed.append(current)
            i = j
        
        return smoothed
