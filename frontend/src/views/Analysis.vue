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
        <span style="font-size: 18px; font-weight: 600">分析结果</span>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="主题分布" name="topics">
          <el-table :data="topicStats" stripe v-loading="loading" style="width: 100%">
            <el-table-column prop="topic" label="主题" min-width="200" />
            <el-table-column prop="count" label="数量" width="100" />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="发现" name="findings">
          <div v-if="!findings.length && !loading" style="text-align: center; padding: 40px; color: #909399">
            暂无发现，请先运行工作流
          </div>
          <el-card
            v-for="f in findings"
            :key="f.id"
            shadow="hover"
            style="margin-bottom: 12px"
          >
            <div style="display: flex; justify-content: space-between; align-items: start">
              <div>
                <strong>{{ f.title }}</strong>
                <el-tag
                  :type="confidenceType(f.confidence)"
                  size="small"
                  style="margin-left: 8px"
                >
                  {{ f.confidence }}
                </el-tag>
                <el-tag
                  :type="f.conclusion_type === 'model' ? 'warning' : 'success'"
                  size="small"
                  effect="plain"
                  style="margin-left: 4px"
                >
                  {{ f.conclusion_type === 'model' ? 'AI 结论' : f.conclusion_type === 'assumption' ? '假设' : '确定性' }}
                </el-tag>
              </div>
              <el-tag type="info" size="small">样本数: {{ f.sample_count }}</el-tag>
            </div>
            <p style="margin: 8px 0; color: #606266">{{ f.description }}</p>
            <div v-if="f.conflicting_evidence" style="font-size: 13px; color: #e6a23c">
              ⚠ 矛盾证据: {{ f.conflicting_evidence }}
            </div>
          </el-card>
        </el-tab-pane>

        <el-tab-pane label="监控 & 成本" name="monitor">
          <el-descriptions v-if="stats" column="3" border>
            <el-descriptions-item label="总 Token">{{ stats.total_tokens }}</el-descriptions-item>
            <el-descriptions-item label="总成本">{{ stats.total_cost }}</el-descriptions-item>
            <el-descriptions-item label="AI 调用次数">{{ stats.ai_call_count }}</el-descriptions-item>
            <el-descriptions-item label="失败次数">{{ stats.ai_fail_count }}</el-descriptions-item>
            <el-descriptions-item label="重试次数">{{ stats.ai_retry_count }}</el-descriptions-item>
            <el-descriptions-item label="耗时">{{ stats.duration_seconds }}秒</el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>
      </el-tabs>
    </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useSessionStore } from '@/stores/session'
import { analysisApi } from '@/api/analysis'
import { monitorApi } from '@/api/monitor'

const session = useSessionStore()
const sessionId = session.sessionId
const activeTab = ref('topics')
const loading = ref(false)
const topicStats = ref<any[]>([])
const findings = ref<any[]>([])
const stats = ref<any>(null)

function confidenceType(c: string) {
  return c === 'high' ? 'success' : c === 'medium' ? 'warning' : 'danger'
}

async function fetchData() {
  if (!sessionId) return
  loading.value = true
  try {
    const [clsRes, findRes, monRes]: any = await Promise.all([
      analysisApi.getClassifications(sessionId),
      analysisApi.getFindings(sessionId),
      monitorApi.getStats(sessionId),
    ])
    const topics: Record<string, { count: number; total: number }> = {}
    ;(clsRes.data || []).forEach((c: any) => {
      if (!topics[c.topic]) topics[c.topic] = { count: 0, total: 0 }
      topics[c.topic].count++
    })
    topicStats.value = Object.entries(topics).map(([topic, v]) => ({
      topic,
      count: (v as any).count,
    }))
    findings.value = findRes.data || []
    stats.value = monRes.data
  } catch {
    // ignore
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>
