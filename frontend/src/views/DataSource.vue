<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <span style="font-size: 18px; font-weight: 600">数据来源说明</span>
      </template>

      <h3 style="margin-top: 0">主要来源：Apple iTunes RSS Feed</h3>
      <el-descriptions v-if="info" column="1" border>
        <el-descriptions-item label="端点" label-width="100">
          <code style="font-size: 12px">{{ info.primary_source.endpoint }}</code>
        </el-descriptions-item>
        <el-descriptions-item label="局限性">
          <ul style="margin: 4px 0; padding-left: 18px">
            <li v-for="lim in info.primary_source.limitations" :key="lim">{{ lim }}</li>
          </ul>
        </el-descriptions-item>
        <el-descriptions-item label="优势">
          <ul style="margin: 4px 0; padding-left: 18px">
            <li v-for="adv in info.primary_source.advantages" :key="adv">{{ adv }}</li>
          </ul>
        </el-descriptions-item>
      </el-descriptions>

      <el-alert
        type="warning"
        show-icon
        :closable="false"
        style="margin-top: 16px"
        title="数据限制说明"
      >
        <template #default>
          <p style="margin: 4px 0">
            Apple RSS 端点已被逐步废弃，约 40% 概率返回空结果。
            采集器内置 3 次自动重试，若仍为空则跳过采集。
          </p>
          <p style="margin: 4px 0">
            建议：如果 RSS 采集不到数据，请使用「导入 JSON/CSV」功能上传评论文件。
            支持的 JSON 格式详见下方说明。
          </p>
        </template>
      </el-alert>
    </el-card>

    <el-card shadow="never" style="margin-top: 16px">
      <template #header>
        <span style="font-size: 18px; font-weight: 600">辅助数据源：文件导入</span>
      </template>

      <el-descriptions v-if="info" column="1" border>
        <el-descriptions-item label="格式" label-width="100">
          {{ info.secondary_source.format }}
        </el-descriptions-item>
        <el-descriptions-item label="必填字段">
          <code>{{ (info.secondary_source.fields.required || []).join(', ') }}</code>
        </el-descriptions-item>
        <el-descriptions-item label="可选字段">
          <code>{{ (info.secondary_source.fields.optional || []).join(', ') }}</code>
        </el-descriptions-item>
        <el-descriptions-item label="用途">
          {{ info.secondary_source.use_case }}
        </el-descriptions-item>
      </el-descriptions>

      <el-collapse style="margin-top: 12px">
        <el-collapse-item title="JSON 格式示例">
          <pre style="font-size: 12px; background: #f5f7fa; padding: 12px; border-radius: 4px; overflow-x: auto">[
  {
    "review_id": "unique_id_001",
    "author": "user1",
    "rating": 5,
    "title": "Great app",
    "content": "I love this app!",
    "version": "3.2.1",
    "reviewed_at": "2026-06-15T10:30:00Z"
  }
]</pre>
        </el-collapse-item>
        <el-collapse-item title="CSV 格式示例">
          <pre style="font-size: 12px; background: #f5f7fa; padding: 12px; border-radius: 4px; overflow-x: auto">review_id,author,rating,title,content,version,reviewed_at
001,user1,5,Great app,I love this app!,3.2.1,2026-06-15T10:30:00Z</pre>
        </el-collapse-item>
      </el-collapse>
    </el-card>

    <el-card shadow="never" style="margin-top: 16px">
      <template #header>
        <span style="font-size: 18px; font-weight: 600">缓存数据</span>
      </template>

      <el-descriptions v-if="info" column="1" border>
        <el-descriptions-item label="目录" label-width="100">
          <code>{{ info.cached_data.path }}</code>
        </el-descriptions-item>
        <el-descriptions-item label="缓存文件">
          <template v-if="info.cached_data.files.length">
            <div v-for="f in info.cached_data.files" :key="f">
              <el-tag size="small" type="warning" style="margin-right: 6px">缓存</el-tag>
              <code>{{ f }}</code>
            </div>
          </template>
          <span v-else>暂无缓存文件</span>
        </el-descriptions-item>
        <el-descriptions-item label="说明">
          {{ info.cached_data.note }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card shadow="never" style="margin-top: 16px">
      <template #header>
        <span style="font-size: 18px; font-weight: 600">数据使用说明</span>
      </template>

      <el-descriptions v-if="info" column="1" border>
        <el-descriptions-item label="AI 分析" label-width="100">
          {{ info.data_usage.note }}
        </el-descriptions-item>
        <el-descriptions-item label="可追溯性">
          {{ info.data_usage.traceability }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { dataSourceApi } from '@/api/dataSource'

const info = ref<any>(null)

onMounted(async () => {
  try {
    const res: any = await dataSourceApi.getInfo()
    info.value = res.data
  } catch {
    // ignore
  }
})
</script>