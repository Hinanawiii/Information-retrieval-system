<template>
  <div
    class="min-h-screen bg-gray-100 flex flex-col items-center justify-center"
  >
    <div class="text-center">
      <h1 class="text-9xl font-bold text-gray-800">404</h1>
      <h2 class="text-2xl font-semibold text-gray-600 mt-4">页面未找到</h2>
      <p class="text-gray-500 mt-2">抱歉，您请求的页面不存在。</p>
      <router-link
        to="/"
        class="mt-8 inline-block px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition duration-200"
      >
        返回首页
      </router-link>
    </div>
  </div>
</template>

<script setup>
// 无需任何逻辑
</script>
