<template>
  <div class="knowledge-page">
    <header class="page-header">
      <el-button text @click="router.push('/')">返回对话</el-button>
      <h2>知识库管理</h2>
    </header>
    <el-empty description="知识库管理界面将在接入后端服务后开放。" />
  </div>
</template>
<script setup lang="ts">
import { useRouter } from 'vue-router'
const router = useRouter()
</script>
<style scoped>
.knowledge-page { max-width: 1200px; margin: 0 auto; min-height: 100vh; background: #fff; padding: 20px; }
.page-header { display: flex; align-items: center; gap: 16px; margin-bottom: 24px; }
</style>
