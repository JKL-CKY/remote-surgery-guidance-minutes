import whisper
import re
from typing import List, Dict, Any, Tuple
from ..core.config import settings
from ..models.schemas import TranscriptSegment
from .speaker_diarization import SpeakerDiarization


class TranscriptionService:
    def __init__(self):
        self.model_name = settings.WHISPER_MODEL
        self.language = settings.WHISPER_LANGUAGE
        self.model = None
        self.speaker_diarization = SpeakerDiarization()
        
        self.anatomical_terms = [
            "动脉", "静脉", "神经", "肌肉", "肌腱", "韧带", "骨骼", "关节",
            "心脏", "肝脏", "脾脏", "肺脏", "肾脏", "胰腺", "胆囊", "胃",
            "小肠", "大肠", "阑尾", "直肠", "膀胱", "前列腺", "子宫", "卵巢",
            "大脑", "小脑", "脑干", "脊髓", "食管", "气管", "支气管",
            "甲状腺", "肾上腺", "淋巴结", "淋巴管", "胸膜", "腹膜", "心包",
            "腹主动脉", "下腔静脉", "门静脉", "胆管", "胰管", "输尿管",
            "尿道", "输精管", "输卵管", "阴道", "阴茎", "睾丸", "附睾",
            "乳腺", "甲状腺", "甲状旁腺", "垂体", "松果体", "胸腺",
            "左叶", "右叶", "上叶", "下叶", "中叶", "尾叶", "方叶",
            "肝门", "肾门", "肺门", "脾门", "胆囊三角", "网膜孔",
            "腹股沟管", "股管", "股三角", "腘窝", "腋窝", "肘窝",
            "膈", "膈肌", "腹膜后", "腹膜内", "腹膜外",
            "肠系膜", "大网膜", "小网膜", "阔韧带", "圆韧带",
            "腹股沟疝", "切口疝", "脐疝", "股疝"
        ]
        
        self.surgery_steps = [
            "切皮", "切开", "分离", "止血", "结扎", "缝合", "吻合", "切除",
            "清扫", "重建", "修复", "移植", "植入", "固定", "复位",
            "探查", "穿刺", "活检", "引流", "灌洗",
            "麻醉", "消毒", "铺巾", "标记", "定位",
            "建立气腹", "置入戳卡", "置入Trocar", "放置引流管",
            "关闭腹腔", "缝合切口", "包扎",
            "淋巴结清扫", "血管吻合", "胃肠吻合", "胆道吻合",
            "肿瘤切除", "病变切除", "病灶清除"
        ]

    def load_model(self):
        if self.model is None:
            self.model = whisper.load_model(self.model_name)
        return self.model

    def transcribe_segment(self, audio_path: str) -> List[TranscriptSegment]:
        model = self.load_model()
        
        result = model.transcribe(
            audio_path,
            language=self.language,
            word_timestamps=True,
            verbose=False
        )
        
        speaker_segments = self.speaker_diarization.diarize(audio_path)
        
        transcript_segments = []
        
        for seg in result["segments"]:
            start_time = float(seg["start"])
            end_time = float(seg["end"])
            text = seg["text"].strip()
            confidence = float(seg.get("avg_logprob", 0))
            
            speaker = self._match_speaker(start_time, end_time, speaker_segments)
            speaker_role = self._classify_speaker_role(speaker)
            
            is_anatomical, detected_terms = self._detect_anatomical_terms(text)
            is_step, step_name = self._detect_surgery_step(text)
            
            transcript_segments.append(TranscriptSegment(
                speaker=speaker,
                speaker_role=speaker_role,
                start_time=start_time,
                end_time=end_time,
                text=text,
                confidence=confidence,
                is_anatomical_term=is_anatomical,
                anatomical_terms=detected_terms if detected_terms else None,
                is_surgery_step=is_step,
                surgery_step=step_name
            ))
        
        return transcript_segments

    def _match_speaker(self, start_time: float, end_time: float, 
                       speaker_segments: List[Dict[str, Any]]) -> str:
        if not speaker_segments:
            return "未知"
        
        mid_time = (start_time + end_time) / 2
        best_match = None
        best_overlap = 0
        
        for seg in speaker_segments:
            seg_start = seg["start_time"]
            seg_end = seg["end_time"]
            
            overlap_start = max(start_time, seg_start)
            overlap_end = min(end_time, seg_end)
            overlap = max(0, overlap_end - overlap_start)
            
            if overlap > best_overlap:
                best_overlap = overlap
                best_match = seg["speaker"]
        
        return best_match if best_match else "未知"

    def _classify_speaker_role(self, speaker: str) -> str:
        if speaker == "SPEAKER_00":
            return "主刀医生"
        elif speaker == "SPEAKER_01":
            return "远程专家"
        else:
            return "其他"

    def _detect_anatomical_terms(self, text: str) -> Tuple[bool, List[str]]:
        detected = []
        for term in self.anatomical_terms:
            if term in text:
                detected.append(term)
        return len(detected) > 0, detected

    def _detect_surgery_step(self, text: str) -> Tuple[bool, str]:
        for step in self.surgery_steps:
            if step in text:
                return True, step
        
        patterns = [
            (r"现在(开始|进行).*", "开始操作"),
            (r"下一步.*", "下一步骤"),
            (r"正在.*", "操作进行中"),
            (r"完成.*", "完成步骤"),
            (r"准备.*", "准备工作"),
        ]
        
        for pattern, step_name in patterns:
            if re.search(pattern, text):
                return True, step_name
        
        return False, None

    def transcribe_and_save(self, session_id: int, audio_path: str, db):
        segments = self.transcribe_segment(audio_path)
        
        from ..core.database import Transcript
        
        for seg in segments:
            transcript = Transcript(
                session_id=session_id,
                speaker=seg.speaker,
                speaker_role=seg.speaker_role,
                start_time=seg.start_time,
                end_time=seg.end_time,
                text=seg.text,
                confidence=seg.confidence,
                is_anatomical_term=seg.is_anatomical_term,
                anatomical_terms=seg.anatomical_terms,
                is_surgery_step=seg.is_surgery_step,
                surgery_step=seg.surgery_step
            )
            db.add(transcript)
        
        db.commit()

    def get_surgery_timeline(self, segments: List[TranscriptSegment]) -> List[Dict[str, Any]]:
        timeline = []
        current_step = None
        
        for seg in segments:
            if seg.is_surgery_step and seg.surgery_step != current_step:
                current_step = seg.surgery_step
                timeline.append({
                    "time": seg.start_time,
                    "step": current_step,
                    "description": seg.text,
                    "speaker": seg.speaker
                })
        
        return timeline

    def merge_segments(self, segments: List[TranscriptSegment], 
                       max_gap: float = 2.0) -> List[TranscriptSegment]:
        if not segments:
            return []
        
        merged = []
        current = segments[0]
        
        for seg in segments[1:]:
            if (seg.start_time - current.end_time <= max_gap and 
                seg.speaker == current.speaker):
                current.end_time = seg.end_time
                current.text += " " + seg.text
                current.confidence = min(current.confidence, seg.confidence)
                
                if seg.is_anatomical_term:
                    current.is_anatomical_term = True
                    if current.anatomical_terms and seg.anatomical_terms:
                        current.anatomical_terms = list(set(
                            current.anatomical_terms + seg.anatomical_terms
                        ))
                    elif seg.anatomical_terms:
                        current.anatomical_terms = seg.anatomical_terms
                
                if seg.is_surgery_step and not current.is_surgery_step:
                    current.is_surgery_step = True
                    current.surgery_step = seg.surgery_step
            else:
                merged.append(current)
                current = seg
        
        merged.append(current)
        return merged
