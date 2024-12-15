<template>
  <div class="search-result-item p-4 border-b hover:bg-gray-50">
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
      <a
        :href="result.url"
        class="text-green-600 hover:underline truncate"
        target="_blank"
      >
        {{ result.url }}
      </a>
    </div>
  </div>
</template>

<script setup>
import { computed, defineProps } from 'vue';

const props = defineProps({
  result: {
    type: Object,
    required: true,
  },
});

// 优先使用高亮的标题，否则使用原始标题
const title = computed(() => {
  return props.result.title_highlight || props.result.title;
});

// 优先使用高亮的内容，否则使用格式化的原始内容
const content = computed(() => {
  return props.result.content_highlight || formatContent(props.result.content);
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
</script>

<style scoped>
:deep(em) {
  color: #e11d48;
  font-style: normal;
  font-weight: bold;
}
</style>
