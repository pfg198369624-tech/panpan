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
          <span style="font-size: 18px; font-weight: 600">评论数据</span>
          <el-radio-group v-model="viewMode" size="small">
            <el-radio-button value="raw">原始</el-radio-button>
            <el-radio-button value="cleaned">清洗后</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <el-table :data="reviews" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="rating" label="评分" width="80" />
        <el-table-column prop="author" label="作者" width="140" />
        <el-table-column label="内容" min-width="400">
          <template #default="{ row }">
            <div style="max-height: 60px; overflow: hidden; text-overflow: ellipsis">
              {{ viewMode === 'raw' ? row.content : row.content_clean }}
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本" width="100" />
        <el-table-column prop="reviewed_at" label="时间" width="160" />
      </el-table>
    </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useSessionStore } from '@/stores/session'
import { reviewsApi } from '@/api/reviews'

const session = useSessionStore()
const sessionId = session.sessionId
const viewMode = ref('raw')
const reviews = ref<any[]>([])
const loading = ref(false)

async function fetchReviews() {
  if (!sessionId) return
  loading.value = true
  try {
    const api = viewMode.value === 'raw' ? reviewsApi.getRaw : reviewsApi.getCleaned
    const res: any = await api(sessionId)
    reviews.value = res.data || []
  } catch {
    reviews.value = []
  } finally {
    loading.value = false
  }
}

watch(viewMode, fetchReviews)
onMounted(fetchReviews)
</script>
