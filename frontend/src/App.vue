<template>
  <el-container style="height: 100vh; overflow: hidden">
    <el-aside width="220px" style="background: #304156; height: 100vh; display: flex; flex-direction: column; overflow: hidden">
      <div style="padding: 20px; color: #fff; font-size: 18px; font-weight: bold; text-align: center; flex-shrink: 0">
        应用评论分析
      </div>
      <div style="flex: 1; overflow-y: auto; overflow-x: hidden">
        <el-menu
          :default-active="route.path"
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
          style="border-right: none"
          @select="handleMenuSelect"
        >
        <el-menu-item index="/">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </el-menu-item>
        <el-menu-item index="/workflow">
          <el-icon><Monitor /></el-icon>
          <span>工作流</span>
        </el-menu-item>
        <el-menu-item index="/reviews">
          <el-icon><ChatDotSquare /></el-icon>
          <span>评论</span>
        </el-menu-item>
        <el-menu-item index="/analysis">
          <el-icon><DataAnalysis /></el-icon>
          <span>分析结果</span>
        </el-menu-item>
        <el-menu-item index="/prd">
          <el-icon><Document /></el-icon>
          <span>PRD</span>
        </el-menu-item>
        <el-menu-item index="/test-cases">
          <el-icon><List /></el-icon>
          <span>测试用例</span>
        </el-menu-item>
        <el-menu-item index="/data-source">
          <el-icon><InfoFilled /></el-icon>
          <span>数据源</span>
        </el-menu-item>
        <el-divider style="border-color: #4a5a6e; margin: 6px 16px" />
        <el-sub-menu index="history" :disabled="session.historyList.length === 0">
          <template #title>
            <el-icon><Clock /></el-icon>
            <span>历史会话</span>
          </template>
          <el-menu-item
            v-for="s in session.historyList"
            :key="s.id"
            :index="'h-' + s.id"
          >
            <div style="display: flex; align-items: center; width: 100%; gap: 6px">
              <span
                :style="{
                  display: 'inline-block',
                  width: '8px', height: '8px', borderRadius: '50%',
                  background: statusDot(s.status),
                  flexShrink: 0,
                }"
              />
              <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; min-width: 0">
                {{ s.app_name || s.app_id || s.id }}
                <template v-if="s.prd_count || s.test_case_count">
                  <span style="font-size: 11px; color: #8a9eb0; margin-left: 4px">
                    P{{ s.prd_count }} T{{ s.test_case_count }}
                  </span>
                </template>
              </div>
            </div>
          </el-menu-item>
        </el-sub-menu>
      </el-menu>
    </div>
    </el-aside>
    <el-container style="height: 100vh; overflow: hidden">
      <el-header style="background: #fff; border-bottom: 1px solid #e6e6e6; display: flex; align-items: center; justify-content: space-between; height: 48px; flex-shrink: 0">
        <span style="font-size: 16px; font-weight: 500">App Review Insights</span>
        <div style="display: flex; align-items: center; gap: 12px">
          <el-tag v-if="session.sessionId" type="info" effect="plain">
            会话: {{ session.sessionId }}
          </el-tag>
          <el-button v-if="session.sessionId" size="small" text @click="doClear">
            退出
          </el-button>
        </div>
      </el-header>
      <el-main style="background: #f0f2f5; overflow-y: auto; height: calc(100vh - 48px)">
        <router-view :key="route.fullPath + '-' + (session.sessionId || '')" />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSessionStore } from '@/stores/session'

const route = useRoute()
const router = useRouter()
const session = useSessionStore()

function handleMenuSelect(index: string) {
  if (index.startsWith('h-')) {
    const sid = index.slice(2)
    const s = session.historyList.find((x: any) => x.id === sid)
    if (s) {
      session.switchSession(s.id, s.app_url || '', s.user_goal || '')
      router.push('/reviews')
    }
    return
  }
  router.push(index)
}

function statusDot(status: string) {
  const map: Record<string, string> = {
    success: '#67C23A', failed: '#F56C6C', running: '#E6A23C',
    created: '#909399', no_data: '#909399',
  }
  return map[status] || '#909399'
}

function doClear() {
  session.clearSession()
  if (route.path !== '/') {
    router.push('/')
  }
}

onMounted(() => {
  session.loadHistory()
})
</script>