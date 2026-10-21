<template>
  <div class="quick-reply-bar">
    <span class="quick-reply-hint">快捷回复:</span>
    <div class="quick-reply-list">
      <el-button
        v-for="(reply, index) in replies"
        :key="index"
        size="small"
        round
        @click="$emit('select', reply)"
      >
        {{ reply }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ replies: string[] }>()
defineEmits<{ (e: 'select', text: string): void }>()
</script>

<style scoped>
.quick-reply-bar { padding: 10px 20px; background: #fafafa; border-top: 1px solid #ebeef5; }
.quick-reply-hint { font-size: 11px; color: #909399; display: block; margin-bottom: 6px; }
.quick-reply-list { display: flex; flex-wrap: wrap; gap: 6px; }
.quick-reply-list .el-button { background: #fff; border-color: #dcdfe6; color: #606266; font-size: 12px; }
.quick-reply-list .el-button:hover { background: #667eea; border-color: #667eea; color: #fff; }
</style>
