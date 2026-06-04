import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Form, Input, Select, Card, message } from 'antd'
import { PlayCircleOutlined, UserOutlined, VideoCameraOutlined, EnvironmentOutlined } from '@ant-design/icons'
import { surgeryApi } from '../services/api'
import type { SurgerySession } from '../types'

interface SessionFormData {
  patient_id: string
  patient_name: string
  surgery_type: string
  primary_surgeon: string
  remote_expert: string
  operating_room: string
  video_source?: string
  audio_source?: string
}

export const CreateSessionPage: React.FC = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm<SessionFormData>()

  const handleSubmit = async (values: SessionFormData) => {
    setLoading(true)
    try {
      const session = await surgeryApi.createSession(values)
      message.success('手术会话创建成功！')
      navigate(`/surgery/${session.session_id}`)
    } catch (error) {
      message.error('创建失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl mb-4 shadow-lg">
            <VideoCameraOutlined className="text-4xl text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">达芬奇手术纪要系统</h1>
          <p className="text-gray-500">创建新的远程手术指导会议</p>
        </div>

        <Card className="shadow-xl border-0">
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
            size="large"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Form.Item
                name="patient_id"
                label="患者ID"
                rules={[{ required: true, message: '请输入患者ID' }]}
              >
                <Input prefix={<UserOutlined />} placeholder="请输入患者ID" />
              </Form.Item>

              <Form.Item
                name="patient_name"
                label="患者姓名"
                rules={[{ required: true, message: '请输入患者姓名' }]}
              >
                <Input prefix={<UserOutlined />} placeholder="请输入患者姓名" />
              </Form.Item>
            </div>

            <Form.Item
              name="surgery_type"
              label="手术类型"
              rules={[{ required: true, message: '请选择手术类型' }]}
            >
              <Select placeholder="请选择手术类型">
                <Select.Option value="腹腔镜胆囊切除术">腹腔镜胆囊切除术</Select.Option>
                <Select.Option value="腹腔镜阑尾切除术">腹腔镜阑尾切除术</Select.Option>
                <Select.Option value="腹腔镜胃癌根治术">腹腔镜胃癌根治术</Select.Option>
                <Select.Option value="腹腔镜结肠癌切除术">腹腔镜结肠癌切除术</Select.Option>
                <Select.Option value="腹腔镜直肠癌切除术">腹腔镜直肠癌切除术</Select.Option>
                <Select.Option value="腹腔镜肝切除术">腹腔镜肝切除术</Select.Option>
                <Select.Option value="腹腔镜胰十二指肠切除术">腹腔镜胰十二指肠切除术</Select.Option>
                <Select.Option value="腹腔镜脾切除术">腹腔镜脾切除术</Select.Option>
                <Select.Option value="腹腔镜肾上腺切除术">腹腔镜肾上腺切除术</Select.Option>
                <Select.Option value="腹腔镜肾切除术">腹腔镜肾切除术</Select.Option>
                <Select.Option value="胸腔镜肺叶切除术">胸腔镜肺叶切除术</Select.Option>
                <Select.Option value="胸腔镜食管癌切除术">胸腔镜食管癌切除术</Select.Option>
                <Select.Option value="机器人辅助前列腺切除术">机器人辅助前列腺切除术</Select.Option>
                <Select.Option value="机器人辅助子宫切除术">机器人辅助子宫切除术</Select.Option>
                <Select.Option value="其他">其他</Select.Option>
              </Select>
            </Form.Item>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Form.Item
                name="primary_surgeon"
                label="主刀医生"
                rules={[{ required: true, message: '请输入主刀医生姓名' }]}
              >
                <Input placeholder="请输入主刀医生姓名" />
              </Form.Item>

              <Form.Item
                name="remote_expert"
                label="远程指导专家"
                rules={[{ required: true, message: '请输入远程专家姓名' }]}
              >
                <Input placeholder="请输入远程专家姓名" />
              </Form.Item>
            </div>

            <Form.Item
              name="operating_room"
              label="手术室"
              rules={[{ required: true, message: '请输入手术室编号' }]}
            >
              <Input prefix={<EnvironmentOutlined />} placeholder="例如：手术室1号" />
            </Form.Item>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Form.Item name="video_source" label="视频源URL (可选)">
                <Input placeholder="RTSP/HLS视频流地址" />
              </Form.Item>

              <Form.Item name="audio_source" label="音频源URL (可选)">
                <Input placeholder="音频流地址" />
              </Form.Item>
            </div>

            <Form.Item className="mb-0">
              <Button
                type="primary"
                htmlType="submit"
                size="large"
                loading={loading}
                icon={<PlayCircleOutlined />}
                className="w-full h-12 text-lg bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 border-0"
              >
                开始手术会议
              </Button>
            </Form.Item>
          </Form>
        </Card>
      </div>
    </div>
  )
}
