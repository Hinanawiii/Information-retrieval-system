<template>
  <div
    class="home-container flex flex-col items-center justify-center min-h-screen bg-gray-50"
  >
    <!-- Logo组件 -->
    <LogoComponent class="mb-8" />

    <!-- 搜索框容器 -->
    <div class="w-full max-w-2xl px-4">
      <div class="relative">
        <input
          v-model="searchQuery"
          type="text"
          class="w-full px-4 py-3 rounded-full border border-gray-300 focus:outline-none focus:border-blue-500 shadow-sm"
          placeholder="输入搜索内容..."
          @keyup.enter="handleSearch"
        />
        <button
          @click="handleSearch"
          class="absolute right-3 top-1/2 transform -translate-y-1/2 px-6 py-2 bg-blue-500 text-white rounded-full hover:bg-blue-600 transition duration-200"
        >
          搜索
        </button>
      </div>

      <!-- 搜索建议列表 -->
      <div
        v-if="suggestions.length > 0"
        class="mt-2 bg-white rounded-lg shadow-lg border border-gray-200"
      >
        <ul>
          <li
            v-for="(suggestion, index) in suggestions"
            :key="index"
            class="px-4 py-2 hover:bg-gray-100 cursor-pointer"
            @click="selectSuggestion(suggestion)"
          >
            {{ suggestion }}
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import LogoComponent from '@/components/LogoComponent.vue';

const router = useRouter();
const searchQuery = ref('');
const suggestions = ref([]);

// 监听搜索输入
watch(searchQuery, async (newQuery) => {
  if (newQuery.trim()) {
    try {
      // TODO: 调用后端API获取搜索建议
      const response = await fetch(
        `/api/suggest?q=${encodeURIComponent(newQuery)}`
      );
      const data = await response.json();
      suggestions.value = data.suggestions;
    } catch (error) {
      console.error('获取搜索建议失败:', error);
      suggestions.value = [];
    }
  } else {
    suggestions.value = [];
  }
});

// 处理搜索
const handleSearch = () => {
  if (searchQuery.value.trim()) {
    router.push({
      name: 'search',
      query: { q: searchQuery.value },
    });
  }
};

// 选择搜索建议
const selectSuggestion = (suggestion) => {
  searchQuery.value = suggestion;
  handleSearch();
};
</script>

<style scoped>
.home-container {
  background-image: linear-gradient(to bottom, #ffffff, #f8f9fa);
}
</style>
