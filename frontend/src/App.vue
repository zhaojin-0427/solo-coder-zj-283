<template>
  <el-container class="app-container">
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <el-icon :size="32" color="#e91e63"><Tools /></el-icon>
        <span class="title">手工布艺管理</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#fce4ec"
        text-color="#333"
        active-text-color="#e91e63"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>数据概览</span>
        </el-menu-item>
        <el-menu-item index="/materials">
          <el-icon><Collection /></el-icon>
          <span>材料库</span>
        </el-menu-item>
        <el-menu-item index="/projects">
          <el-icon><Folder /></el-icon>
          <span>作品档案</span>
        </el-menu-item>
        <el-menu-item index="/photos">
          <el-icon><Picture /></el-icon>
          <span>过程相册</span>
        </el-menu-item>
        <el-menu-item index="/costs">
          <el-icon><Money /></el-icon>
          <span>成本核算</span>
        </el-menu-item>
        <el-menu-item index="/orders">
          <el-icon><Tickets /></el-icon>
          <span>订单管理</span>
        </el-menu-item>
        <el-menu-item index="/statistics">
          <el-icon><TrendCharts /></el-icon>
          <span>统计分析</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item>{{ currentPage }}</el-breadcrumb-item>
        </el-breadcrumb>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const activeMenu = computed(() => route.path)

const pageNames = {
  '/dashboard': '数据概览',
  '/materials': '材料库',
  '/projects': '作品档案',
  '/photos': '过程相册',
  '/costs': '成本核算',
  '/orders': '订单管理',
  '/statistics': '统计分析'
}

const currentPage = computed(() => {
  let path = route.path
  if (path.startsWith('/projects/')) {
    path = '/projects'
  } else if (path.startsWith('/orders/')) {
    path = '/orders'
  }
  return pageNames[path] || '首页'
})
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.sidebar {
  background: linear-gradient(180deg, #fce4ec 0%, #f8bbd9 100%);
  border-right: 1px solid #f8bbd9;
}

.logo {
  display: flex;
  align-items: center;
  padding: 24px 20px;
  gap: 12px;
  border-bottom: 1px solid rgba(233, 30, 99, 0.2);
}

.logo .title {
  font-size: 18px;
  font-weight: 600;
  color: #ad1457;
}

:deep(.el-menu) {
  border-right: none;
}

:deep(.el-menu-item) {
  height: 50px;
  line-height: 50px;
  margin: 4px 8px;
  border-radius: 8px;
}

:deep(.el-menu-item.is-active) {
  background-color: #e91e63 !important;
  color: white !important;
}

.header {
  background: white;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  padding: 0 24px;
}

.main-content {
  background-color: #fafafa;
  padding: 24px;
  overflow-y: auto;
}
</style>
