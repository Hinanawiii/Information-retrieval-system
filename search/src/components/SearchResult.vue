<template>
  <div class="search-result-item p-4 border-b hover:bg-gray-50">
    <div class="flex">
      <!-- 主要内容区 -->
      <div class="flex-grow">
        <h3 class="text-xl mb-2">
          <a
            :href="result.url"
            class="text-blue-600 hover:underline"
            target="_blank"
            v-html="title"
          ></a>
        </h3>
        <p class="text-gray-600 mb-2 text-sm" v-html="content"></p>
        <div class="flex items-center text-sm text-gray-500 space-x-4">
          <span>
            <i class="fas fa-building mr-1"></i>
            {{ result.department || '未知部门' }}
          </span>
          <span v-if="result.pagerank_score" class="flex items-center">
            <i class="fas fa-chart-line mr-1"></i>
            相关度: {{ formatScore(result.pagerank_score) }}
          </span>
          <span v-if="result.publish_time" class="flex items-center">
            <i class="fas fa-calendar mr-1"></i>
            {{ result.publish_time }}
          </span>
          <!-- 快照链接 -->
          <a
            :href="`/snapshot/${encodeURIComponent(result.title)}.png`"
            target="_blank"
            class="text-blue-500 hover:underline flex items-center"
          >
            <i class="fas fa-camera mr-1"></i>
            网页快照
          </a>
          <a
            :href="result.url"
            class="text-green-600 hover:underline truncate"
            target="_blank"
          >
            {{ result.url }}
          </a>
        </div>
      </div>

      <!-- 快照预览 -->
      <div class="ml-4 w-32 flex-shrink-0">
        <img
          :src="`/snapshot/${encodeURIComponent(result.title)}.png`"
          :alt="result.title"
          class="w-full h-24 object-cover rounded border"
          @error="onImageError"
          v-if="showSnapshot"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';

// 定义 props
const result = defineProps({
  result: {
    type: Object,
    required: true,
  },
});

// 控制快照显示
const showSnapshot = ref(true);

// 优先使用高亮的标题，否则使用原始标题
const title = computed(() => {
  return result.result.title_highlight || result.result.title;
});

// 优先使用高亮的内容，否则使用格式化的原始内容
const content = computed(() => {
  return (
    result.result.content_highlight || formatContent(result.result.content)
  );
});

// 格式化内容，截取合适长度
const formatContent = (text) => {
  if (!text) return '无内容预览';
  return text.length > 200 ? text.slice(0, 200) + '...' : text;
};

// 格式化分数
const formatScore = (score) => {
  return (score * 100).toFixed(2);
};

// 处理图片加载错误
const onImageError = () => {
  showSnapshot.value = false;
};
</script>

<style scoped>
:deep(em) {
  color: #e11d48;
  font-style: normal;
  font-weight: bold;
}
</style>
