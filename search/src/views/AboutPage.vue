<template>
  <div class="min-h-screen bg-gray-50 py-12">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="bg-white rounded-lg shadow-lg p-8">
        <!-- 标题 -->
        <h1 class="text-3xl font-bold text-gray-900 mb-8">关于搜索引擎</h1>

        <!-- 项目介绍 -->
        <section class="mb-8">
          <h2 class="text-2xl font-semibold text-gray-800 mb-4">项目简介</h2>
          <p class="text-gray-600 leading-relaxed mb-4">
            这是一个基于 Vue.js、Elasticsearch 和 Python
            开发的搜索引擎系统。本项目旨在提供高效、准确的校园信息搜索服务。
          </p>
        </section>

        <!-- 主要功能 -->
        <section class="mb-8">
          <h2 class="text-2xl font-semibold text-gray-800 mb-4">主要功能</h2>
          <ul class="list-disc list-inside text-gray-600 space-y-2">
            <li>全文搜索支持</li>
            <li>关键词高亮显示</li>
            <li>智能搜索建议</li>
            <li>基于 PageRank 的搜索结果排序</li>
            <li>多种搜索模式（标准搜索、短语搜索、通配符搜索）</li>
            <li>部门和时间筛选</li>
            <li>用户搜索历史记录</li>
            <li>个性化推荐</li>
          </ul>
        </section>

        <!-- 技术栈 -->
        <section class="mb-8">
          <h2 class="text-2xl font-semibold text-gray-800 mb-4">技术栈</h2>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div class="p-4 bg-gray-50 rounded-lg">
              <h3 class="font-semibold text-gray-700 mb-2">前端</h3>
              <ul class="text-gray-600 text-sm space-y-1">
                <li>Vue 3</li>
                <li>Vue Router</li>
                <li>Tailwind CSS</li>
              </ul>
            </div>
            <div class="p-4 bg-gray-50 rounded-lg">
              <h3 class="font-semibold text-gray-700 mb-2">后端</h3>
              <ul class="text-gray-600 text-sm space-y-1">
                <li>Python</li>
                <li>Flask</li>
                <li>MongoDB</li>
              </ul>
            </div>
            <div class="p-4 bg-gray-50 rounded-lg">
              <h3 class="font-semibold text-gray-700 mb-2">搜索引擎</h3>
              <ul class="text-gray-600 text-sm space-y-1">
                <li>Elasticsearch</li>
                <li>Scrapy</li>
                <li>PageRank</li>
              </ul>
            </div>
          </div>
        </section>

        <!-- 版本信息 -->
        <section>
          <div class="text-center text-gray-500 text-sm">
            <p>版本：1.0.0</p>
            <p>最后更新：{{ new Date().getFullYear() }}</p>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
// 无需额外逻辑
</script>
