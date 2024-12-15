import { createRouter, createWebHistory } from 'vue-router';

// 导入组件
import HomePage from '@/views/HomePage.vue';
import SearchPage from '@/views/SearchPage.vue';
import DetailedPage from '@/views/DetailedPage.vue';
import LoginComponent from '@/components/LoginComponent.vue';
import AboutPage from '@/views/AboutPage.vue';

// 创建路由
const routes = [
  {
    path: '/',
    name: 'home',
    component: HomePage,
    meta: {
      title: '首页 - 搜索引擎',
    },
  },
  {
    path: '/search',
    name: 'search',
    component: SearchPage,
    meta: {
      title: '搜索结果 - 搜索引擎',
    },
  },
  {
    path: '/detail/:id',
    name: 'detail',
    component: DetailedPage,
    meta: {
      title: '详情页 - 搜索引擎',
    },
  },
  {
    path: '/login',
    name: 'login',
    component: LoginComponent,
    meta: {
      title: '登录 - 搜索引擎',
    },
  },
  {
    path: '/about',
    name: 'about',
    component: AboutPage,
    meta: {
      title: '关于 - 搜索引擎',
    },
  },
  // 404页面
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/views/NotFound.vue'),
    meta: {
      title: '页面未找到 - 搜索引擎',
    },
  },
];

// 创建路由实例
const router = createRouter({
  history: createWebHistory(),
  routes,
});

// 路由守卫
router.beforeEach((to, from, next) => {
  // 更新页面标题
  document.title = to.meta.title || '搜索引擎';

  // 检查是否需要登录权限
  // const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  // const isAuthenticated = localStorage.getItem('isAuthenticated');

  // if (requiresAuth && !isAuthenticated) {
  //   next('/login');
  // } else {
  //   next();
  // }

  next();
});

export default router;
