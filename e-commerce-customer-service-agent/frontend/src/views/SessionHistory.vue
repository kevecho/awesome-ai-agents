<template>
  <div class="history-page">
    <header class="page-header">
      <el-button text @click="router.push('/')">返回对话</el-button>
      <h2>历史会话</h2>
    </header>
    <el-empty description="接入数据库后，此处将展示历史会话记录。" />
  </div>
</template>
<script setup lang="ts">
import { useRouter } from 'vue-router'
const router = useRouter()
</script>
<style scoped>
.history-page { max-width: 1200px; margin: 0 auto; min-height: 100vh; background: #fff; padding: 20px; }
.page-header { display: flex; align-items: center; gap: 16px; margin-bottom: 24px; }
</style>
