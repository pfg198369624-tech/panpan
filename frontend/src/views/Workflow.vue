<template>
  <div>
    <el-card v-if="!session.sessionId" shadow="never">
      <el-empty description="当前无活跃会话">
        <template #description>
          <span>请从左侧导航选择历史会话，或回到<router-link to="/">首页</router-link>开始新分析</span>
        </template>
      </el-empty>
    </el-card>
    <template v-else>
      <el-card shadow="never">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span style="font-size: 18px; font-weight: 600">工作流进度</span>
          <div>
            <el-tag v-if="sessionId" type="info" style="margin-right: 8px">{{ sessionId }}</el-tag>
            <el-tag v-if="workflowStatus === 'no_data'" type="info">无数据</el-tag>
            <el-tag v-else-if="workflowDone && workflowStatus === 'success'" type="success">已完成</el-tag>
            <el-tag v-else-if="workflowDone && workflowStatus === 'failed'" type="danger">失败</el-tag>
            <el-tag v-else type="warning" effect="dark">
              <span class="dot-pulse"></span> 运行中
            </el-tag>
          </div>
        </div>
      </template>

      <el-steps :active="activeStep" align-center finish-status="success" style="margin: 20px 0">
        <el-step
          v-for="(s, i) in stepList"
          :key="i"
          :title="s.title"
          :description="s.desc"
          :status="stepStatus(i + 1)"
        />
      </el-steps>

      <el-alert
        v-if="workflowStatus === 'no_data'"
        title="未获取到评论数据"
        type="warning"
        :description="'US App Store RSS 未返回该应用的评论数据。您可以通过「数据源」页面上传 JSON/CSV 格式的评论文件进行离线分析。'"
        show-icon
        closable
        style="margin-bottom: 16px"
      />

      <div v-if="!timeline.length" style="text-align: center; padding: 40px; color: #909399">
        等待工作流启动...
      </div>

      <el-timeline v-else>
        <el-timeline-item
          v-for="(item, i) in timeline"
          :key="i"
          :timestamp="item.time"
          :type="item.type"
          :hollow="item.type === 'primary'"
        >
          <strong>{{ item.label }}</strong>
          <span v-if="item.status === 'success'" style="color: #67c23a; margin-left: 8px">✓</span>
          <span v-else-if="item.status === 'failed'" style="color: #f56c6c; margin-left: 8px">✗</span>
          <span v-else-if="item.status === 'running'" style="color: #409EFF; margin-left: 8px">⟳</span>
          <div v-if="item.detail" style="margin-top: 4px; font-size: 13px; color: #606266">
            {{ item.detail }}
          </div>
          <div v-if="item.error" style="margin-top: 4px; font-size: 13px; color: #f56c6c">
            {{ item.error }}
          </div>
        </el-timeline-item>
      </el-timeline>
    </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useSessionStore } from '@/stores/session'
import { workflowApi } from '@/api/workflow'

const session = useSessionStore()
const sessionId = session.sessionId
const activeStep = ref(0)
const stepStatuses = ref<Record<number, string>>({})
const timeline = ref<any[]>([])
const workflowDone = ref(false)
const workflowStatus = ref('')
let ws: WebSocket | null = null
let pollTimer: ReturnType<typeof setInterval> | null = null
let lastLogCount = 0

const stepList = [
  { title: '分析范围', desc: '确定分析范围' },
  { title: '采集', desc: '采集评论数据' },
  { title: '清洗', desc: '清洗去重' },
  { title: '分析', desc: 'AI 单次分析' },
  { title: 'PRD', desc: '生成需求文档' },
  { title: '测试', desc: '生成测试用例' },
  { title: '验证', desc: '追溯链验证' },
]

function stepStatus(step: number) {
  if (stepStatuses.value[step] === 'success') return 'success'
  if (stepStatuses.value[step] === 'failed') return 'error'
  if (stepStatuses.value[step] === 'skipped') return 'finish'
  if (stepStatuses.value[step] === 'running') return 'process'
  if (activeStep.value >= step) return 'finish'
  return 'wait'
}

function connectWs() {
  if (!sessionId) return
  const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
  const host = baseUrl.replace('/api', '').replace('http://', '')
  const wsUrl = `ws://${host}/api/workflow/${sessionId}/ws`
  try {
    ws = new WebSocket(wsUrl)
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        handleWsMessage(msg)
      } catch { /* ignore */ }
    }
    ws.onclose = () => { ws = null }
    ws.onerror = () => { ws = null }
  } catch { /* ws not available */ }
}

function handleWsMessage(msg: any) {
  if (msg.type === 'step_update') {
    stepStatuses.value[msg.step] = msg.status
    if (msg.status === 'running') {
      activeStep.value = msg.step - 1
      addTimelineItem(msg.step, msg.status, msg.message || stepList[msg.step - 1]?.title || '')
    } else if (msg.status === 'success') {
      activeStep.value = msg.step
      addTimelineItem(msg.step, msg.status, msg.message || `${stepList[msg.step - 1]?.title || ''} 完成`)
    } else if (msg.status === 'failed') {
      addTimelineItem(msg.step, msg.status, msg.message || `${stepList[msg.step - 1]?.title || ''} 失败`)
    } else if (msg.status === 'skipped') {
      activeStep.value = msg.step
      addTimelineItem(msg.step, 'info', msg.message || '跳过')
    }
  } else if (msg.type === 'log') {
    addTimelineItem(parseInt(msg.step), msg.status, msg.log)
  } else if (msg.type === 'workflow_complete') {
    workflowDone.value = true
    workflowStatus.value = msg.status || 'success'
    stopPolling()
    closeWs()
  }
}

function addTimelineItem(step: number, status: string, message: string) {
  const now = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  const label = stepList[step - 1]?.title || `步骤${step}`
  timeline.value.push({
    time: now,
    type: status === 'success' ? 'success' : status === 'failed' ? 'danger' : status === 'info' ? 'info' : 'primary',
    label,
    status,
    detail: status === 'success' || status === 'running' ? message : undefined,
    error: status === 'failed' ? message : undefined,
  })
}

async function pollStatus() {
  if (!sessionId || workflowDone.value) return
  try {
    const [statusRes, logsRes]: any = await Promise.all([
      workflowApi.getStatus(sessionId),
      workflowApi.getLogs(sessionId),
    ])
    const step = statusRes.data?.current_step || 0
    if (step > activeStep.value) activeStep.value = step
    const wfStatus = statusRes.data?.status || ''
    if (['success', 'failed', 'no_data'].includes(wfStatus)) {
      workflowDone.value = true
      workflowStatus.value = wfStatus
      stopPolling()
      closeWs()
    }

    const logs = logsRes.data || []
    if (logs.length > lastLogCount) {
      for (let i = lastLogCount; i < logs.length; i++) {
        const log = logs[i]
        stepStatuses.value[parseInt(log.step)] = log.status
        const label = stepList[parseInt(log.step) - 1]?.title || `步骤${log.step}`
        const time = log.finished_at || log.started_at || ''
        const exists = timeline.value.some(
          (t) => t.label === label && t.time === time
        )
        if (!exists) {
          timeline.value.push({
            time: time ? new Date(time).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) : '',
            type: log.status === 'success' ? 'success' : log.status === 'failed' ? 'danger' : 'primary',
            label,
            status: log.status,
            detail: log.output_summary || undefined,
            error: log.error_message || undefined,
          })
        }
      }
      lastLogCount = logs.length
    }
  } catch { /* ignore */ }
}

function startPolling() {
  pollStatus()
  pollTimer = setInterval(pollStatus, 2000)
}

function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

function closeWs() {
  if (ws) { ws.close(); ws = null }
}

onMounted(() => {
  connectWs()
  startPolling()
})

onUnmounted(() => {
  closeWs()
  stopPolling()
})
</script>

<style scoped>
.dot-pulse {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #fff;
  animation: pulse 1.2s ease-in-out infinite;
  margin-right: 4px;
  vertical-align: middle;
}
@keyframes pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}
</style>
