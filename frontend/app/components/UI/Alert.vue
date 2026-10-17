<template>
	<div v-if="text" class="flex gap-2 rounded-lg bg-red-50 text-red-700 dark:bg-red-950/50 dark:text-red-300 px-3 py-2.5 text-sm whitespace-pre-line">
		<Icon name="lucide:circle-alert" class="shrink-0 mt-0.5" size="16" />
		<span>{{ text }}</span>
	</div>
</template>

<script lang="ts" setup>
defineProps<{ text?: string }>()
</script>
