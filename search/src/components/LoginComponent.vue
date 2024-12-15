<template>
  <div
    class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8"
  >
    <div class="max-w-md w-full space-y-8">
      <!-- Logo和标题 -->
      <div class="text-center">
        <LogoComponent class="mx-auto w-32" />
        <h2 class="mt-6 text-3xl font-extrabold text-gray-900">
          登录到搜索系统
        </h2>
      </div>

      <!-- 登录表单 -->
      <form class="mt-8 space-y-6" @submit.prevent="handleLogin">
        <!-- 错误消息 -->
        <div v-if="error" class="text-red-500 text-center text-sm">
          {{ error }}
        </div>

        <!-- 用户名输入 -->
        <div>
          <label for="username" class="sr-only">用户名</label>
          <input
            id="username"
            v-model="username"
            name="username"
            type="text"
            required
            class="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
            placeholder="用户名"
          />
        </div>

        <!-- 密码输入 -->
        <div>
          <label for="password" class="sr-only">密码</label>
          <input
            id="password"
            v-model="password"
            name="password"
            type="password"
            required
            class="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
            placeholder="密码"
          />
        </div>

        <!-- 记住我选项 -->
        <div class="flex items-center justify-between">
          <div class="flex items-center">
            <input
              id="remember-me"
              v-model="rememberMe"
              name="remember-me"
              type="checkbox"
              class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label for="remember-me" class="ml-2 block text-sm text-gray-900">
              记住我
            </label>
          </div>
        </div>

        <!-- 登录按钮 -->
        <div>
          <button
            type="submit"
            :disabled="loading"
            class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            <span class="absolute left-0 inset-y-0 flex items-center pl-3">
              <i class="fas fa-lock"></i>
            </span>
            {{ loading ? '登录中...' : '登录' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import LogoComponent from './LogoComponent.vue';

const router = useRouter();

// 状态变量
const username = ref('');
const password = ref('');
const rememberMe = ref(false);
const loading = ref(false);
const error = ref('');

// 登录处理
const handleLogin = async () => {
  if (loading.value) return;

  loading.value = true;
  error.value = '';

  try {
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: username.value,
        password: password.value,
      }),
    });

    const data = await response.json();

    if (response.ok) {
      // 如果选择了"记住我"，保存用户信息
      if (rememberMe.value) {
        localStorage.setItem('username', username.value);
      } else {
        localStorage.removeItem('username');
      }

      // 登录成功，重定向到首页
      router.push('/');
    } else {
      error.value = data.error || '登录失败';
    }
  } catch (err) {
    error.value = '网络错误，请稍后重试';
  } finally {
    loading.value = false;
  }
};

// 检查是否有保存的用户名
if (localStorage.getItem('username')) {
  username.value = localStorage.getItem('username');
  rememberMe.value = true;
}
</script>
