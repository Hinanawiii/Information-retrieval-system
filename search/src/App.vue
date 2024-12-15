<template>
  <div class="app">
    <!-- 顶部导航栏 -->
    <nav class="bg-white shadow-sm" v-if="showNavBar">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex">
            <!-- Logo -->
            <div class="flex-shrink-0 flex items-center">
              <router-link to="/" class="text-xl font-bold text-gray-800">
                搜索引擎
              </router-link>
            </div>
          </div>

          <!-- 右侧导航链接 -->
          <div class="flex items-center">
            <router-link
              to="/about"
              class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
            >
              关于
            </router-link>
            <router-link
              v-if="!isAuthenticated"
              to="/login"
              class="ml-4 text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
            >
              登录
            </router-link>
            <button
              v-else
              @click="handleLogout"
              class="ml-4 text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
            >
              退出
            </button>
          </div>
        </div>
      </div>
    </nav>

    <!-- 路由视图 -->
    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const route = useRoute();
const router = useRouter();

// 计算是否显示导航栏（在首页不显示）
const showNavBar = computed(() => route.path !== '/');

// 用户认证状态（可以后续与状态管理集成）
const isAuthenticated = ref(false);

// 退出登录
const handleLogout = () => {
  isAuthenticated.value = false;
  localStorage.removeItem('isAuthenticated');
  router.push('/');
};

// 检查登录状态
if (localStorage.getItem('isAuthenticated')) {
  isAuthenticated.value = true;
}
</script>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
