<template>
	<div class="flex gap-3" :class="{ 'flex-row-reverse': message.role === 'user' }">
		<div
			class="w-8 h-8 rounded-full flex-center shrink-0"
			:class="message.role === 'user' ? 'bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-200' : 'bg-primary-600 text-white'"
		>
			<Icon :name="message.role === 'user' ? 'lucide:user' : 'lucide:sparkles'" size="16" />
		</div>

		<div class="max-w-[85%] sm:max-w-[75%]" :class="{ 'text-right': message.role === 'user' }">
			<div
				class="inline-block text-left rounded-2xl px-4 py-2.5 text-[15px] leading-relaxed whitespace-pre-line break-words"
				:class="message.role === 'user' ? 'bg-primary-600 text-white rounded-tr-sm' : 'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-tl-sm'"
			>
				<template v-if="message.content">{{ message.content }}</template>
				<span v-else class="inline-flex gap-1 py-1.5">
					<span v-for="i in 3" :key="i" class="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" :style="{ animationDelay: `${i * 0.15}s` }" />
				</span>
			</div>

			<div v-if="message.citations.length" class="flex flex-wrap gap-1.5 mt-2">
				<span
					v-for="citation in message.citations"
					:key="citation.chunk_id"
					:title="`“${citation.cited_text}”`"
					class="inline-flex items-center gap-1 rounded-md bg-slate-100 dark:bg-slate-800 px-2 py-1 text-xs text-slate-600 dark:text-slate-300 cursor-help"
				>
					<Icon name="lucide:file-text" size="12" />
					{{ citation.document_title }}<template v-if="citation.page"> · p. {{ citation.page }}</template>
				</span>
			</div>
		</div>
	</div>
</template>

<script lang="ts" setup>
import type { ChatMessage } from '~/types'

interface Props {
	message: ChatMessage
}
defineProps<Props>()
</script>
