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
        <span style="font-size: 18px; font-weight: 600">产品需求文档</span>
      </template>

      <el-tabs v-model="activeVersion" v-if="versions.length">
        <el-tab-pane
          v-for="v in versions"
          :key="v.version_no"
          :label="`${v.version_no} - ${v.name}`"
          :name="v.version_no"
        >
          <el-table :data="requirementsByVersion(v.id)" stripe style="width: 100%">
            <el-table-column prop="req_id" label="编号" width="100" />
            <el-table-column prop="title" label="标题" min-width="250" />
            <el-table-column prop="description" label="描述" min-width="300" />
            <el-table-column label="优先级" width="100">
              <template #default="{ row }">
                <el-tag :type="row.priority === 'P0' ? 'danger' : row.priority === 'P1' ? 'warning' : 'info'" size="small">
                  {{ row.priority }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag type="info" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>

      <div v-if="!versions.length" style="text-align: center; padding: 40px; color: #909399">
        暂无 PRD，请先运行工作流
      </div>
    </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useSessionStore } from '@/stores/session'
import { prdApi } from '@/api/prd'

const session = useSessionStore()
const sessionId = session.sessionId
const versions = ref<any[]>([])
const requirements = ref<any[]>([])
const activeVersion = ref('')

function requirementsByVersion(versionId: number) {
  return requirements.value.filter((r) => r.version_id === versionId)
}

onMounted(async () => {
  if (!sessionId) return
  try {
    const [verRes, reqRes]: any = await Promise.all([
      prdApi.getVersions(sessionId),
      prdApi.getRequirements(sessionId),
    ])
    versions.value = verRes.data || []
    requirements.value = reqRes.data || []
    if (versions.value.length) activeVersion.value = versions.value[0].version_no
  } catch {
    // ignore
  }
})
</script>
