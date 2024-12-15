<template>
  <div class="logo-container">
    <router-link to="/" class="block">
      <img
        src="@/assets/logo.png"
        alt="Search Engine Logo"
        class="w-48 h-auto transition-transform duration-300 hover:scale-105"
      />
    </router-link>
  </div>
</template>

<script setup>
// 这是一个简单的展示组件，不需要任何JavaScript逻辑
</script>

<style scoped>
.logo-container {
  user-select: none;
}
</style>
