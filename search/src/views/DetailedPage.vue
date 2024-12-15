<template>
  <div class="min-h-screen bg-gray-50 py-8">
    <div class="container mx-auto px-4">
      <!-- 返回按钮 -->
      <button
        @click="$router.back()"
        class="mb-6 flex items-center text-gray-600 hover:text-gray-900"
      >
        <span class="mr-2">←</span> 返回搜索结果
      </button>

      <!-- 主要内容 -->
      <div class="bg-white rounded-lg shadow-lg p-6">
        <!-- 加载状态 -->
        <div v-if="loading" class="flex justify-center items-center h-64">
          <div
            class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"
          ></div>
        </div>

        <!-- 错误状态 -->
        <div v-else-if="error" class="text-center text-red-500 py-8">
          {{ error }}
        </div>

        <!-- 内容展示 -->
        <div v-else>
          <!-- 标题 -->
          <h1 class="text-2xl font-bold text-gray-900 mb-4">
            {{ document.title }}
          </h1>

          <!-- 元信息 -->
          <div class="flex flex-wrap gap-4 text-sm text-gray-500 mb-6">
            <div class="flex items-center">
              <i class="fas fa-building mr-2"></i>
              <span>部门：{{ document.department || '未知' }}</span>
            </div>
            <div class="flex items-center">
              <i class="fas fa-chart-line mr-2"></i>
              <span>相关度：{{ formatPageRank(document.pagerank_score) }}</span>
            </div>
            <div class="flex items-center">
              <i class="fas fa-link mr-2"></i>
              <a
                :href="document.url"
                target="_blank"
                class="text-blue-500 hover:underline"
              >
                访问原始页面
              </a>
            </div>
          </div>

          <!-- 正文内容 -->
          <div class="prose max-w-none">
            <div v-html="formattedContent"></div>
          </div>

          <!-- 相关链接 -->
          <div
            v-if="document.outlinks && document.outlinks.length"
            class="mt-8"
          >
            <h2 class="text-xl font-semibold mb-4">相关链接</h2>
            <ul class="space-y-2">
              <li v-for="(link, index) in document.outlinks" :key="index">
                <a
                  :href="link"
                  target="_blank"
                  class="text-blue-500 hover:underline block truncate"
                >
                  {{ getAnchorText(link) }}
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();
const document = ref(null);
const loading = ref(true);
const error = ref(null);

// 格式化 PageRank 分数
const formatPageRank = (score) => {
  if (!score) return '未知';
  return (score * 100).toFixed(2);
};

// 获取链接的锚文本
const getAnchorText = (url) => {
  if (!document.value || !document.value.anchor_texts) return url;

  const anchorText = document.value.anchor_texts.find((a) => a.url === url);
  return anchorText ? anchorText.text : url;
};

// 格式化内容，将换行符转换为HTML段落
const formattedContent = computed(() => {
  if (!document.value || !document.value.content) return '';
  return document.value.content
    .split('\n')
    .filter((p) => p.trim())
    .map((p) => `<p>${p}</p>`)
    .join('');
});

// 获取文档详情
const fetchDocument = async () => {
  const documentId = route.params.id;
  if (!documentId) {
    error.value = '未找到文档ID';
    loading.value = false;
    return;
  }

  try {
    const response = await fetch(`/api/documents/${documentId}`);
    if (!response.ok) throw new Error('获取文档失败');

    const data = await response.json();
    document.value = data;
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
};

onMounted(fetchDocument);
</script>

<style scoped>
.prose {
  @apply text-gray-800 leading-relaxed;
}

.prose p {
  @apply mb-4;
}
</style>
