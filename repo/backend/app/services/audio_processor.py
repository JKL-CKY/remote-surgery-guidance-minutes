import numpy as np
import librosa
import soundfile as sf
import os
from scipy import signal
from scipy.io import wavfile
from typing import Dict, Any, List, Tuple
from ..core.config import settings


class AudioProcessor:
    def __init__(self):
        self.sample_rate = settings.AUDIO_SAMPLE_RATE
        self.channels = settings.AUDIO_CHANNELS
        self.noise_reduction_strength = settings.NOISE_REDUCTION_STRENGTH
        
        self.scalpel_freq_min = settings.ELECTRIC_SCALPEL_FREQ_MIN
        self.scalpel_freq_max = settings.ELECTRIC_SCALPEL_FREQ_MAX
        self.alarm_freq_min = settings.MONITOR_ALARM_FREQ_MIN
        self.alarm_freq_max = settings.MONITOR_ALARM_FREQ_MAX

    def load_audio(self, file_path: str) -> Tuple[np.ndarray, int]:
        y, sr = librosa.load(file_path, sr=self.sample_rate, mono=True)
        return y, sr

    def save_audio(self, y: np.ndarray, file_path: str, sr: int = None):
        if sr is None:
            sr = self.sample_rate
        sf.write(file_path, y, sr)

    def detect_electric_scalpel(self, y: np.ndarray, sr: int) -> Tuple[bool, float]:
        D = np.abs(librosa.stft(y))
        frequencies = librosa.fft_frequencies(sr=sr)
        
        freq_mask = (frequencies >= self.scalpel_freq_min) & (frequencies <= self.scalpel_freq_max)
        energy_in_band = np.mean(D[freq_mask, :])
        total_energy = np.mean(D)
        
        if total_energy > 0:
            ratio = energy_in_band / total_energy
        else:
            ratio = 0
        
        detected = ratio > 0.3
        return detected, float(ratio)

    def detect_monitor_alarm(self, y: np.ndarray, sr: int) -> Tuple[bool, List[float]]:
        D = np.abs(librosa.stft(y))
        frequencies = librosa.fft_frequencies(sr=sr)
        
        freq_mask = (frequencies >= self.alarm_freq_min) & (frequencies <= self.alarm_freq_max)
        band_spectrum = np.mean(D[freq_mask, :], axis=0)
        
        peak_indices = signal.find_peaks(band_spectrum, height=np.mean(band_spectrum) * 2, distance=sr // 4)[0]
        alarm_times = []
        
        for idx in peak_indices:
            time = librosa.frames_to_time(idx, sr=sr)
            alarm_times.append(float(time))
        
        detected = len(peak_indices) > 0
        return detected, alarm_times

    def spectral_subtraction(self, y: np.ndarray, sr: int, noise_estimation_duration: float = 0.5) -> np.ndarray:
        n_fft = 2048
        hop_length = 512
        
        noise_samples = int(noise_estimation_duration * sr)
        noise_clip = y[:noise_samples] if len(y) > noise_samples else y
        
        D_noise = np.abs(librosa.stft(noise_clip, n_fft=n_fft, hop_length=hop_length))
        noise_mag = np.mean(D_noise, axis=1, keepdims=True)
        
        D = librosa.stft(y, n_fft=n_fft, hop_length=hop_length)
        mag = np.abs(D)
        phase = np.angle(D)
        
        alpha = 2
        beta = 0.01
        mag_clean = np.maximum(mag - alpha * noise_mag, beta * mag)
        
        D_clean = mag_clean * np.exp(1j * phase)
        y_clean = librosa.istft(D_clean, hop_length=hop_length, length=len(y))
        
        return y_clean

    def notch_filter(self, y: np.ndarray, sr: int, freq: float, q: float = 30.0) -> np.ndarray:
        b, a = signal.iirnotch(freq, q, sr)
        y_filtered = signal.filtfilt(b, a, y)
        return y_filtered

    def band_stop_filter(self, y: np.ndarray, sr: int, freq_min: int, freq_max: int) -> np.ndarray:
        nyquist = sr / 2
        low = freq_min / nyquist
        high = freq_max / nyquist
        order = 4
        b, a = signal.butter(order, [low, high], btype='bandstop')
        y_filtered = signal.filtfilt(b, a, y)
        return y_filtered

    def remove_electric_scalpel_noise(self, y: np.ndarray, sr: int) -> np.ndarray:
        y_clean = self.band_stop_filter(y, sr, self.scalpel_freq_min, self.scalpel_freq_max)
        
        harmonic_freqs = [1000, 2000, 3000, 4000]
        for freq in harmonic_freqs:
            if self.scalpel_freq_min <= freq <= self.scalpel_freq_max:
                y_clean = self.notch_filter(y_clean, sr, freq)
        
        return y_clean

    def remove_monitor_alarm(self, y: np.ndarray, sr: int) -> np.ndarray:
        y_clean = y
        alarm_freqs = [880, 1000, 1200, 1760, 2000, 2400, 3200]
        for freq in alarm_freqs:
            if self.alarm_freq_min <= freq <= self.alarm_freq_max:
                y_clean = self.notch_filter(y_clean, sr, freq, q=50)
        return y_clean

    def wiener_filter(self, y: np.ndarray) -> np.ndarray:
        y_denoised = signal.wiener(y, mysize=5)
        return y_denoised

    def process_audio_segment(
        self,
        file_path: str,
        session_id: str,
        segment_index: int
    ) -> Dict[str, Any]:
        y, sr = self.load_audio(file_path)
        
        has_scalpel, scalpel_ratio = self.detect_electric_scalpel(y, sr)
        has_alarm, alarm_times = self.detect_monitor_alarm(y, sr)
        
        y_processed = y.copy()
        noise_reduction_applied = False
        
        if has_scalpel:
            y_processed = self.remove_electric_scalpel_noise(y_processed, sr)
            noise_reduction_applied = True
        
        if has_alarm:
            y_processed = self.remove_monitor_alarm(y_processed, sr)
            noise_reduction_applied = True
        
        y_processed = self.spectral_subtraction(y_processed, sr)
        y_processed = self.wiener_filter(y_processed)
        noise_reduction_applied = True
        
        output_dir = os.path.join(settings.STORAGE_PATH, session_id, "processed")
        os.makedirs(output_dir, exist_ok=True)
        
        output_filename = f"segment_{segment_index:06d}_processed.wav"
        output_path = os.path.join(output_dir, output_filename)
        self.save_audio(y_processed, output_path, sr)
        
        duration = len(y) / sr
        
        return {
            "segment_index": segment_index,
            "file_path": output_path,
            "start_time": segment_index * 30.0,
            "end_time": (segment_index + 1) * 30.0,
            "duration": duration,
            "has_electric_scalpel": has_scalpel,
            "scalpel_noise_ratio": scalpel_ratio,
            "has_monitor_alarm": has_alarm,
            "alarm_times": alarm_times,
            "noise_reduction_applied": noise_reduction_applied,
            "original_path": file_path,
            "processed_path": output_path
        }

    def process_full_session(self, session_id: str, db_session_id: int):
        input_dir = os.path.join(settings.STORAGE_PATH, session_id, "raw")
        if not os.path.exists(input_dir):
            return
        
        audio_files = sorted([
            f for f in os.listdir(input_dir)
            if f.endswith(('.wav', '.mp3', '.flac', '.m4a'))
        ])
        
        for idx, audio_file in enumerate(audio_files):
            file_path = os.path.join(input_dir, audio_file)
            self.process_audio_segment(file_path, session_id, idx)

    def real_time_process_chunk(self, audio_chunk: bytes) -> bytes:
        y = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
        
        sr = self.sample_rate
        has_scalpel, _ = self.detect_electric_scalpel(y, sr)
        has_alarm, _ = self.detect_monitor_alarm(y, sr)
        
        if has_scalpel:
            y = self.remove_electric_scalpel_noise(y, sr)
        if has_alarm:
            y = self.remove_monitor_alarm(y, sr)
        
        y = self.spectral_subtraction(y, sr)
        
        processed_chunk = (y * 32768.0).astype(np.int16).tobytes()
        return processed_chunk
