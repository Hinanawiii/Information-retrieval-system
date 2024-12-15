<template>
  <div class="min-h-screen bg-gray-50">
    <!-- 顶部搜索栏 -->
    <div class="bg-white shadow-sm sticky top-0 z-10">
      <div class="container mx-auto px-4 py-3">
        <div class="flex items-center space-x-4">
          <router-link to="/" class="shrink-0">
            <LogoComponent class="w-24" />
          </router-link>
          <div class="flex-grow">
            <div class="relative">
              <input
                v-model="searchQuery"
                type="text"
                class="w-full px-4 py-2 pr-10 rounded-lg border focus:outline-none focus:border-blue-500"
                placeholder="输入搜索内容..."
                @keyup.enter="handleSearch"
              />
              <button
                @click="handleSearch"
                class="absolute right-2 top-1/2 transform -translate-y-1/2 px-4 py-1 bg-blue-500 text-white rounded-md hover:bg-blue-600"
              >
                搜索
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 主要内容区 -->
    <div class="container mx-auto px-4 py-6">
      <div class="grid grid-cols-12 gap-6">
        <!-- 左侧筛选器 -->
        <div class="col-span-3">
          <div class="bg-white rounded-lg shadow p-4">
            <h3 class="text-lg font-medium mb-4">筛选器</h3>

            <!-- 部门筛选 -->
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-2">
                部门
              </label>
              <select
                v-model="filters.department"
                class="w-full border rounded-md px-3 py-2"
                @change="handleSearch"
              >
                <option value="">全部部门</option>
                <option v-for="dept in departments" :key="dept" :value="dept">
                  {{ dept }}
                </option>
              </select>
            </div>

            <!-- 搜索类型 -->
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-2">
                搜索类型
              </label>
              <select
                v-model="filters.type"
                class="w-full border rounded-md px-3 py-2"
                @change="handleSearch"
              >
                <option value="standard">标准搜索</option>
                <option value="phrase">短语搜索</option>
                <option value="wildcard">通配符搜索</option>
              </select>
            </div>

            <!-- 排序方式 -->
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-2">
                排序方式
              </label>
              <select
                v-model="filters.sortBy"
                class="w-full border rounded-md px-3 py-2"
                @change="handleSearch"
              >
                <option value="pagerank_score">相关度</option>
                <option value="publish_time">发布时间</option>
              </select>
            </div>
          </div>
        </div>

        <!-- 右侧搜索结果 -->
        <div class="col-span-9">
          <!-- 搜索统计 -->
          <div class="mb-4 text-sm text-gray-600">
            找到约 {{ totalResults }} 个结果 (用时 {{ searchTime }}秒)
          </div>

          <!-- 搜索结果列表 -->
          <div class="bg-white rounded-lg shadow">
            <div v-if="loading" class="p-8 text-center text-gray-500">
              <div
                class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"
              ></div>
              正在搜索...
            </div>
            <div
              v-else-if="results.length === 0"
              class="p-8 text-center text-gray-500"
            >
              没有找到相关结果
            </div>
            <template v-else>
              <SearchResult
                v-for="result in results"
                :key="result.url"
                :result="result"
              />
            </template>
          </div>

          <!-- 分页 -->
          <div v-if="totalPages > 1" class="mt-6 flex justify-center">
            <div class="flex space-x-2">
              <button
                v-for="page in displayedPages"
                :key="page"
                @click="handlePageChange(page)"
                :class="[
                  'px-3 py-1 rounded',
                  currentPage === page
                    ? 'bg-blue-500 text-white'
                    : 'bg-white text-blue-500 hover:bg-gray-100',
                ]"
              >
                {{ page }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import LogoComponent from '@/components/LogoComponent.vue';
import SearchResult from '@/components/SearchResult.vue';

const route = useRoute();
const router = useRouter();

// 状态
const searchQuery = ref('');
const results = ref([]);
const loading = ref(false);
const totalResults = ref(0);
const searchTime = ref(0);
const currentPage = ref(1);
const departments = ref([]);

// 筛选器状态
const filters = ref({
  department: '',
  type: 'standard',
  sortBy: 'pagerank_score',
  sortOrder: 'desc',
});

// 计算属性
const totalPages = computed(() => Math.ceil(totalResults.value / 10));
const displayedPages = computed(() => {
  const pages = [];
  const maxPages = 5;
  let start = Math.max(1, currentPage.value - Math.floor(maxPages / 2));
  let end = Math.min(totalPages.value, start + maxPages - 1);

  if (end - start + 1 < maxPages) {
    start = Math.max(1, end - maxPages + 1);
  }

  for (let i = start; i <= end; i++) {
    pages.push(i);
  }
  return pages;
});

// 方法
const fetchDepartments = async () => {
  try {
    const response = await fetch('/api/departments', {
      headers: {
        Accept: 'application/json',
      },
    });
    if (!response.ok) throw new Error('获取部门列表失败');
    const data = await response.json();
    departments.value = data;
  } catch (error) {
    console.error('获取部门列表失败:', error);
  }
};

const handleSearch = async () => {
  loading.value = true;
  const startTime = Date.now();

  try {
    const queryParams = new URLSearchParams({
      q: searchQuery.value,
      page: currentPage.value.toString(),
      size: '10',
      type: filters.value.type,
      sort_by: filters.value.sortBy,
      sort_order: filters.value.sortOrder,
    });

    if (filters.value.department) {
      queryParams.append('department', filters.value.department);
    }

    console.log(
      'Sending search request to:',
      `/api/search?${queryParams.toString()}`
    );

    const response = await fetch(`/api/search?${queryParams.toString()}`, {
      headers: {
        Accept: 'application/json',
      },
    });

    if (!response.ok) throw new Error('搜索请求失败');

    const data = await response.json();
    console.log('Search response:', data);

    // 修改这里以匹配后端返回的数据结构
    results.value = data.results || [];
    totalResults.value = data.total || 0;
    searchTime.value = ((Date.now() - startTime) / 1000).toFixed(2);

    // 更新 URL
    router.push({
      query: {
        q: searchQuery.value,
        page: currentPage.value,
        ...filters.value,
      },
    });
  } catch (error) {
    console.error('搜索失败:', error);
    results.value = [];
    totalResults.value = 0;
  } finally {
    loading.value = false;
  }
};

const handlePageChange = (page) => {
  currentPage.value = page;
  handleSearch();
};

// 生命周期钩子
onMounted(async () => {
  // 从 URL 获取初始参数
  const { q, page, department, type, sort_by } = route.query;

  searchQuery.value = q || '';
  currentPage.value = parseInt(page) || 1;
  filters.value = {
    department: department || '',
    type: type || 'standard',
    sortBy: sort_by || 'pagerank_score',
    sortOrder: 'desc',
  };

  await fetchDepartments();
  if (searchQuery.value) {
    handleSearch();
  }
});
</script>
