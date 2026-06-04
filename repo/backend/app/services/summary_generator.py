import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from ..core.config import settings
from ..models.schemas import TranscriptSegment, SurgerySummaryResponse


class SummaryGenerator:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.client = None
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)

    def generate_summary(
        self,
        session_id: str,
        transcripts: List[TranscriptSegment],
        session_info: Dict[str, Any]
    ) -> SurgerySummaryResponse:
        if self.client:
            return self._generate_with_openai(transcripts, session_info)
        else:
            return self._generate_fallback(transcripts, session_info)

    def _generate_with_openai(
        self,
        transcripts: List[TranscriptSegment],
        session_info: Dict[str, Any]
    ) -> SurgerySummaryResponse:
        full_transcript = self._format_transcripts(transcripts)
        
        system_prompt = """你是一名专业的外科手术记录分析师，擅长分析远程达芬奇手术指导会议的内容。
请根据手术对话记录，生成结构化的手术纪要，包括手术要点、技术改进建议、并发症风险评估等。
请用中文回答，保持专业性和准确性。"""

        user_prompt = f"""请分析以下远程手术指导会议的内容，并生成结构化纪要：

=== 手术信息 ===
患者姓名: {session_info.get('patient_name', '未知')}
手术类型: {session_info.get('surgery_type', '未知')}
主刀医生: {session_info.get('primary_surgeon', '未知')}
远程指导专家: {session_info.get('remote_expert', '未知')}
手术室: {session_info.get('operating_room', '未知')}
开始时间: {session_info.get('start_time', '未知')}
结束时间: {session_info.get('end_time', '未知')}

=== 对话记录 ===
{full_transcript}

=== 输出要求 ===
请输出JSON格式，包含以下字段：
1. key_points: 手术要点列表（5-10条）
2. surgical_steps: 手术步骤列表，每个步骤包含time、step、description
3. anatomical_landmarks: 涉及的解剖标识列表
4. technical_improvements: 技术改进建议列表
5. complications: 可能的并发症及处理建议列表
6. overall_assessment: 总体评估（200-300字）
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=4096,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return SurgerySummaryResponse(
                key_points=result.get("key_points", []),
                surgical_steps=result.get("surgical_steps", []),
                anatomical_landmarks=result.get("anatomical_landmarks", []),
                technical_improvements=result.get("technical_improvements", []),
                complications=result.get("complications", []),
                overall_assessment=result.get("overall_assessment", "")
            )
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return self._generate_fallback(transcripts, session_info)

    def _generate_fallback(
        self,
        transcripts: List[TranscriptSegment],
        session_info: Dict[str, Any]
    ) -> SurgerySummaryResponse:
        key_points = self._extract_key_points(transcripts)
        surgical_steps = self._extract_surgical_steps(transcripts)
        anatomical_landmarks = self._extract_anatomical_terms(transcripts)
        technical_improvements = self._extract_improvements(transcripts)
        complications = self._extract_complications(transcripts)
        overall_assessment = self._generate_overall_assessment(transcripts, session_info)

        return SurgerySummaryResponse(
            key_points=key_points,
            surgical_steps=surgical_steps,
            anatomical_landmarks=anatomical_landmarks,
            technical_improvements=technical_improvements,
            complications=complications,
            overall_assessment=overall_assessment
        )

    def _format_transcripts(self, transcripts: List[TranscriptSegment]) -> str:
        lines = []
        for t in transcripts:
            time_str = f"[{self._format_time(t.start_time)}]"
            speaker = f"{t.speaker}({t.speaker_role})"
            lines.append(f"{time_str} {speaker}: {t.text}")
        return "\n".join(lines)

    def _format_time(self, seconds: float) -> str:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    def _extract_key_points(self, transcripts: List[TranscriptSegment]) -> List[str]:
        key_points = []
        expert_comments = [t for t in transcripts if t.speaker_role == "远程专家"]
        
        for t in expert_comments[:10]:
            if len(t.text) > 10:
                key_points.append(f"{t.speaker}: {t.text[:100]}")
        
        if not key_points:
            for t in transcripts[:10]:
                if len(t.text) > 10:
                    key_points.append(f"{t.speaker}: {t.text[:100]}")
        
        return key_points

    def _extract_surgical_steps(self, transcripts: List[TranscriptSegment]) -> List[Dict[str, Any]]:
        steps = []
        step_transcripts = [t for t in transcripts if t.is_surgery_step]
        
        for t in step_transcripts:
            steps.append({
                "time": t.start_time,
                "step": t.surgery_step or "手术操作",
                "description": t.text
            })
        
        if not steps:
            for t in transcripts[:20]:
                steps.append({
                    "time": t.start_time,
                    "step": "手术进行中",
                    "description": t.text
                })
        
        return steps

    def _extract_anatomical_terms(self, transcripts: List[TranscriptSegment]) -> List[str]:
        terms = set()
        for t in transcripts:
            if t.anatomical_terms:
                terms.update(t.anatomical_terms)
        return sorted(list(terms))

    def _extract_improvements(self, transcripts: List[TranscriptSegment]) -> List[str]:
        improvements = []
        keywords = ["建议", "应该", "更好", "改进", "注意", "小心", "避免"]
        
        for t in transcripts:
            for kw in keywords:
                if kw in t.text:
                    improvements.append(f"[{t.speaker}] {t.text}")
                    break
        
        return improvements[:10]

    def _extract_complications(self, transcripts: List[TranscriptSegment]) -> List[str]:
        complications = []
        keywords = ["出血", "损伤", "风险", "并发症", "小心", "注意", "避免"]
        
        for t in transcripts:
            for kw in keywords:
                if kw in t.text:
                    complications.append(f"[{self._format_time(t.start_time)}] {t.text}")
                    break
        
        return complications[:10]

    def _generate_overall_assessment(self, transcripts: List[TranscriptSegment], 
                                      session_info: Dict[str, Any]) -> str:
        duration = 0
        if transcripts:
            duration = transcripts[-1].end_time
        
        surgeon_speaking = sum(
            t.end_time - t.start_time 
            for t in transcripts 
            if t.speaker_role == "主刀医生"
        )
        expert_speaking = sum(
            t.end_time - t.start_time 
            for t in transcripts 
            if t.speaker_role == "远程专家"
        )
        
        assessment = f"""
本次{session_info.get('surgery_type', '手术')}由{session_info.get('primary_surgeon', '主刀医生')}主刀，
{session_info.get('remote_expert', '远程专家')}提供远程指导。

手术总时长约{int(duration // 60)}分钟，其中主刀医生发言约{int(surgeon_speaking // 60)}分钟，
远程专家指导约{int(expert_speaking // 60)}分钟。

共记录有效对话{len(transcripts)}条，涉及解剖标识{len(self._extract_anatomical_terms(transcripts))}处。

远程专家在手术过程中提供了{len(self._extract_improvements(transcripts))}条技术建议，
手术过程顺利，主刀与专家配合良好。
        """.strip()
        
        return assessment
