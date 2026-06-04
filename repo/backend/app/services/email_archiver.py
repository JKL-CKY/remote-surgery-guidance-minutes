import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Dict, Any, List
from jinja2 import Template
from ..core.config import settings
from ..models.schemas import TranscriptSegment, SurgerySummaryResponse


class EmailArchiver:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.archive_to = settings.EMAIL_ARCHIVE_TO
        self.subject_prefix = settings.EMAIL_SUBJECT_PREFIX

        self.email_template = Template("""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>手术记录 - {{ session.session_id }}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #1e3c72, #2a5298); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .header h1 { margin: 0; font-size: 24px; }
        .header p { margin: 5px 0 0 0; opacity: 0.9; }
        .section { background: #f9f9f9; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
        .section h2 { color: #1e3c72; border-bottom: 2px solid #2a5298; padding-bottom: 10px; margin-top: 0; }
        .info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }
        .info-item { background: white; padding: 12px; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .info-item strong { color: #1e3c72; display: block; margin-bottom: 5px; }
        .timeline { position: relative; padding-left: 30px; }
        .timeline-item { position: relative; margin-bottom: 15px; padding-bottom: 15px; border-left: 2px solid #2a5298; }
        .timeline-item::before { content: ''; position: absolute; left: -8px; top: 0; width: 14px; height: 14px; background: #2a5298; border-radius: 50%; }
        .timeline-time { font-weight: bold; color: #1e3c72; }
        .timeline-step { color: #e74c3c; font-weight: bold; }
        .timeline-speaker { color: #27ae60; font-style: italic; }
        .keypoints-list, .anatomy-list, .improvements-list, .complications-list { list-style: none; padding: 0; }
        .keypoints-list li, .anatomy-list li, .improvements-list li, .complications-list li {
            background: white; padding: 10px 15px; margin-bottom: 8px; border-radius: 6px;
            border-left: 4px solid #2a5298; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .complications-list li { border-left-color: #e74c3c; }
        .improvements-list li { border-left-color: #27ae60; }
        .assessment { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; }
        .transcript-table { width: 100%; border-collapse: collapse; background: white; border-radius: 6px; overflow: hidden; }
        .transcript-table th, .transcript-table td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        .transcript-table th { background: #1e3c72; color: white; }
        .transcript-table tr:hover { background: #f5f5f5; }
        .role-surgeon { color: #e74c3c; font-weight: bold; }
        .role-expert { color: #3498db; font-weight: bold; }
        .footer { text-align: center; padding: 20px; color: #7f8c8d; font-size: 12px; }
        .badge { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; margin-right: 5px; }
        .badge-step { background: #e74c3c; color: white; }
        .badge-anatomy { background: #f39c12; color: white; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏥 达芬奇手术纪要系统</h1>
        <p>手术记录归档 | 记录编号: {{ session.session_id }} | 生成时间: {{ generated_at }}</p>
    </div>

    <div class="section">
        <h2>📋 手术基本信息</h2>
        <div class="info-grid">
            <div class="info-item"><strong>患者姓名</strong>{{ session.patient_name }}</div>
            <div class="info-item"><strong>患者ID</strong>{{ session.patient_id }}</div>
            <div class="info-item"><strong>手术类型</strong>{{ session.surgery_type }}</div>
            <div class="info-item"><strong>主刀医生</strong>{{ session.primary_surgeon }}</div>
            <div class="info-item"><strong>远程专家</strong>{{ session.remote_expert }}</div>
            <div class="info-item"><strong>手术室</strong>{{ session.operating_room }}</div>
            <div class="info-item"><strong>开始时间</strong>{{ session.start_time }}</div>
            <div class="info-item"><strong>结束时间</strong>{{ session.end_time or '进行中' }}</div>
        </div>
    </div>

    <div class="section">
        <h2>🔑 手术要点</h2>
        <ul class="keypoints-list">
            {% for point in summary.key_points %}
            <li>{{ point }}</li>
            {% endfor %}
        </ul>
    </div>

    <div class="section">
        <h2>📝 手术步骤时间线</h2>
        <div class="timeline">
            {% for step in summary.surgical_steps %}
            <div class="timeline-item">
                <span class="timeline-time">[{{ format_time(step.time) }}]</span>
                <span class="timeline-step">{{ step.step }}</span>
                <p>{{ step.description }}</p>
            </div>
            {% endfor %}
        </div>
    </div>

    <div class="section">
        <h2>🏗️ 解剖标识</h2>
        <ul class="anatomy-list">
            {% for term in summary.anatomical_landmarks %}
            <li>📍 {{ term }}</li>
            {% endfor %}
        </ul>
    </div>

    <div class="section">
        <h2>💡 技术改进建议</h2>
        <ul class="improvements-list">
            {% for imp in summary.technical_improvements %}
            <li>{{ imp }}</li>
            {% endfor %}
        </ul>
    </div>

    <div class="section">
        <h2>⚠️ 并发症风险及处理</h2>
        <ul class="complications-list">
            {% for comp in summary.complications %}
            <li>{{ comp }}</li>
            {% endfor %}
        </ul>
    </div>

    <div class="section">
        <h2>📊 总体评估</h2>
        <div class="assessment">
            {{ summary.overall_assessment }}
        </div>
    </div>

    <div class="section">
        <h2>💬 完整对话记录</h2>
        <table class="transcript-table">
            <thead>
                <tr>
                    <th>时间</th>
                    <th>发言者</th>
                    <th>角色</th>
                    <th>内容</th>
                    <th>标签</th>
                </tr>
            </thead>
            <tbody>
                {% for t in transcripts %}
                <tr>
                    <td>{{ format_time(t.start_time) }}</td>
                    <td>{{ t.speaker }}</td>
                    <td>
                        {% if t.speaker_role == '主刀医生' %}
                        <span class="role-surgeon">主刀医生</span>
                        {% elif t.speaker_role == '远程专家' %}
                        <span class="role-expert">远程专家</span>
                        {% else %}
                        {{ t.speaker_role }}
                        {% endif %}
                    </td>
                    <td>{{ t.text }}</td>
                    <td>
                        {% if t.is_surgery_step %}
                        <span class="badge badge-step">步骤</span>
                        {% endif %}
                        {% if t.is_anatomical_term %}
                        <span class="badge badge-anatomy">解剖</span>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <div class="footer">
        <p>本邮件由达芬奇手术纪要系统自动生成 | 请勿直接回复 | {{ generated_at }}</p>
    </div>
</body>
</html>
        """)

    def format_time(self, seconds: float) -> str:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    def archive_surgery_record(
        self,
        session: Any,
        summary: SurgerySummaryResponse,
        transcripts: List[TranscriptSegment],
        recipient_email: str = None
    ) -> Dict[str, Any]:
        to_email = recipient_email or self.archive_to
        
        try:
            html_content = self._render_email(session, summary, transcripts)
            text_content = self._render_plain_text(session, summary, transcripts)
            
            subject = f"{self.subject_prefix} {session.surgery_type} - {session.patient_name} - {session.session_id}"
            
            msg = MIMEMultipart("alternative")
            msg["From"] = self.from_email
            msg["To"] = to_email
            msg["Subject"] = subject
            msg["X-Surgery-ID"] = session.session_id
            msg["X-Patient-ID"] = session.patient_id
            
            msg.attach(MIMEText(text_content, "plain", "utf-8"))
            msg.attach(MIMEText(html_content, "html", "utf-8"))
            
            transcript_csv = self._generate_transcript_csv(transcripts)
            if transcript_csv:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(transcript_csv.encode("utf-8"))
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename=transcript_{session.session_id}.csv"
                )
                msg.attach(part)
            
            message_id = self._send_email(msg, to_email)
            
            return {
                "success": True,
                "message_id": message_id,
                "recipient": to_email,
                "subject": subject
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "recipient": to_email
            }

    def _render_email(self, session: Any, summary: SurgerySummaryResponse,
                      transcripts: List[TranscriptSegment]) -> str:
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return self.email_template.render(
            session=session,
            summary=summary,
            transcripts=transcripts,
            generated_at=generated_at,
            format_time=self.format_time
        )

    def _render_plain_text(self, session: Any, summary: SurgerySummaryResponse,
                           transcripts: List[TranscriptSegment]) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append("达芬奇手术纪要系统 - 手术记录")
        lines.append("=" * 60)
        lines.append(f"记录编号: {session.session_id}")
        lines.append(f"患者: {session.patient_name} (ID: {session.patient_id})")
        lines.append(f"手术类型: {session.surgery_type}")
        lines.append(f"主刀医生: {session.primary_surgeon}")
        lines.append(f"远程专家: {session.remote_expert}")
        lines.append(f"手术室: {session.operating_room}")
        lines.append(f"开始时间: {session.start_time}")
        lines.append(f"结束时间: {session.end_time or '进行中'}")
        lines.append("")
        
        lines.append("-" * 60)
        lines.append("【手术要点】")
        lines.append("-" * 60)
        for i, point in enumerate(summary.key_points, 1):
            lines.append(f"{i}. {point}")
        lines.append("")
        
        lines.append("-" * 60)
        lines.append("【手术步骤】")
        lines.append("-" * 60)
        for step in summary.surgical_steps:
            lines.append(f"[{self.format_time(step['time'])}] {step['step']}: {step['description']}")
        lines.append("")
        
        lines.append("-" * 60)
        lines.append("【解剖标识】")
        lines.append("-" * 60)
        lines.append(", ".join(summary.anatomical_landmarks))
        lines.append("")
        
        lines.append("-" * 60)
        lines.append("【技术改进建议】")
        lines.append("-" * 60)
        for i, imp in enumerate(summary.technical_improvements, 1):
            lines.append(f"{i}. {imp}")
        lines.append("")
        
        lines.append("-" * 60)
        lines.append("【并发症风险】")
        lines.append("-" * 60)
        for i, comp in enumerate(summary.complications, 1):
            lines.append(f"{i}. {comp}")
        lines.append("")
        
        lines.append("-" * 60)
        lines.append("【总体评估】")
        lines.append("-" * 60)
        lines.append(summary.overall_assessment)
        lines.append("")
        
        lines.append("-" * 60)
        lines.append("【完整对话记录】")
        lines.append("-" * 60)
        for t in transcripts:
            tags = []
            if t.is_surgery_step:
                tags.append("步骤")
            if t.is_anatomical_term:
                tags.append("解剖")
            tag_str = f" [{', '.join(tags)}]" if tags else ""
            lines.append(f"[{self.format_time(t.start_time)}] {t.speaker}({t.speaker_role}): {t.text}{tag_str}")
        
        return "\n".join(lines)

    def _generate_transcript_csv(self, transcripts: List[TranscriptSegment]) -> str:
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["开始时间", "结束时间", "发言者", "角色", "内容", "是否手术步骤", "手术步骤", "是否解剖术语", "解剖术语", "置信度"])
        
        for t in transcripts:
            writer.writerow([
                t.start_time,
                t.end_time,
                t.speaker,
                t.speaker_role,
                t.text,
                t.is_surgery_step,
                t.surgery_step or "",
                t.is_anatomical_term,
                ", ".join(t.anatomical_terms) if t.anatomical_terms else "",
                t.confidence
            ])
        
        return output.getvalue()

    def _send_email(self, msg: MIMEMultipart, to_email: str) -> str:
        if not self.smtp_username or not self.smtp_password:
            print(f"[MOCK EMAIL] Would send to {to_email}: {msg['Subject']}")
            return f"mock-{datetime.now().timestamp()}"
        
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
        
        return msg.get("Message-ID", str(datetime.now().timestamp()))
