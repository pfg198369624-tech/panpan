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
        <span style="font-size: 18px; font-weight: 600">测试用例</span>
      </template>

      <el-table :data="testCases" stripe v-loading="loading" style="width: 100%">
        <el-table-column prop="case_id" label="编号" width="100" />
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="preconditions" label="前置条件" min-width="200" />
        <el-table-column prop="expected_result" label="预期结果" min-width="250" />
        <el-table-column label="关联需求" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.req_id }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'draft' ? 'info' : 'success'" size="small">
              {{ row.status === 'draft' ? '草稿' : '已完成' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useSessionStore } from '@/stores/session'
import { testCasesApi } from '@/api/testCases'

const session = useSessionStore()
const sessionId = session.sessionId
const testCases = ref<any[]>([])
const loading = ref(false)

onMounted(async () => {
  if (!sessionId) return
  loading.value = true
  try {
    const res: any = await testCasesApi.getAll(sessionId)
    testCases.value = res.data || []
  } catch {
    // ignore
  } finally {
    loading.value = false
  }
})
</script>
