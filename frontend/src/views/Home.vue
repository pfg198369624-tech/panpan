<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <span style="font-size: 18px; font-weight: 600">开始新分析</span>
      </template>

      <el-form label-width="120px">
        <el-form-item label="App Store 链接">
          <el-input
            v-model="appUrl"
            placeholder="https://apps.apple.com/us/app/workout-for-women-home-gym/id839285684"
            clearable
          />
        </el-form-item>

        <el-form-item label="分析目标">
          <el-input
            v-model="userGoal"
            placeholder="可选：如「关注订阅转化问题」「分析低分评论原因」"
            type="textarea"
            :rows="2"
            clearable
          />
        </el-form-item>

        <el-form-item>
          <div style="display: flex; gap: 12px">
            <el-button type="primary" size="large" @click="startAnalysis" :loading="loading">
              <el-icon style="margin-right: 6px"><VideoPlay /></el-icon>
              开始分析
            </el-button>
            <el-upload
              action="#"
              :auto-upload="false"
              :show-file-list="false"
              :before-upload="handleImport"
              accept=".json,.csv"
            >
              <el-button size="large" :loading="importing">
                <el-icon style="margin-right: 6px"><Upload /></el-icon>
                导入 JSON/CSV
              </el-button>
            </el-upload>
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="loading" shadow="never" style="margin-top: 16px">
      <el-alert title="工作流已启动" type="success" show-icon :closable="false" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '@/stores/session'
import { workflowApi } from '@/api/workflow'
import api from '@/api/index'
import { ElMessage } from 'element-plus'

const router = useRouter()
const session = useSessionStore()

const appUrl = ref('https://apps.apple.com/us/app/workout-for-women-home-gym/id839285684')
const userGoal = ref('')
const loading = ref(false)
const importing = ref(false)

async function startAnalysis() {
  if (!appUrl.value) {
    ElMessage.warning('请输入 App Store 链接')
    return
  }
  loading.value = true
  try {
    const res: any = await workflowApi.start(appUrl.value, userGoal.value || undefined)
    session.setSession(res.data.session_id, appUrl.value, userGoal.value)
    session.loadHistory()
    router.push('/workflow')
  } catch (err: any) {
    ElMessage.error(err.message || '启动失败')
  } finally {
    loading.value = false
  }
}

async function handleImport(file: File): Promise<boolean> {
  const isJson = file.name.endsWith('.json')
  const isCsv = file.name.endsWith('.csv')
  if (!isJson && !isCsv) {
    ElMessage.warning('仅支持 JSON 或 CSV 文件')
    return false
  }
  importing.value = true
  try {
    const form = new FormData()
    form.append('file', file)
    const endpoint = isJson ? '/import/json' : '/import/csv'
    const res: any = await api.post(endpoint, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    if (res.success) {
      ElMessage.success(`导入 ${res.data.imported} 条评论，工作流已启动`)
      session.setSession(res.data.session_id, '', '')
      session.loadHistory()
      router.push('/workflow')
    } else {
      ElMessage.error(res.error || '导入失败')
    }
  } catch (err: any) {
    ElMessage.error(err.message || '导入失败')
  } finally {
    importing.value = false
  }
  return false
}
</script>
