<template>
	<section class="flex flex-col min-h-0">
		<div class="flex items-center justify-between mb-3">
			<h2 class="text-sm font-semibold text-slate-500 uppercase tracking-wide">Documents</h2>
			<span class="text-xs text-slate-400">{{ store.ready.length }} ready</span>
		</div>

		<label
			ref="dropZone"
			class="flex flex-col items-center justify-center gap-1 rounded-xl border-2 border-dashed px-4 py-5 text-center cursor-pointer transition-300"
			:class="isOverDropZone ? 'border-primary-500 bg-primary-50 dark:bg-primary-600/10' : 'border-slate-200 dark:border-slate-700 hover:border-primary-500'"
		>
			<Icon :name="store.uploading ? 'lucide:loader-circle' : 'lucide:upload'" size="22" :class="['text-primary-600', { 'animate-spin': store.uploading }]" />
			<span class="text-sm font-medium">{{ store.uploading ? 'Uploading…' : 'Drop files or click to upload' }}</span>
			<span class="text-xs text-slate-400">PDF, Word, TXT or Markdown, up to 10 MB</span>
			<input type="file" class="hidden" multiple accept=".pdf,.docx,.txt,.md" :disabled="store.uploading" @change="onPick" />
		</label>
		<UIAlert :text="store.error" class="mt-3" />

		<ul class="mt-3 space-y-1.5 overflow-y-auto scroll-thin min-h-0">
			<li
				v-for="document in store.items"
				:key="document.id"
				class="group flex items-center gap-3 rounded-lg px-2.5 py-2 hover:bg-slate-100 dark:hover:bg-slate-800/60 transition-300"
			>
				<Icon :name="icons[document.content_type] || 'lucide:file-text'" size="18" class="text-slate-400 shrink-0" />
				<div class="flex-1 min-w-0">
					<p class="text-sm font-medium truncate" :title="document.title">{{ document.title }}</p>
					<p v-if="document.status === 'processing'" class="flex items-center gap-1 text-xs text-amber-600">
						<Icon name="lucide:loader-circle" size="12" class="animate-spin" /> Reading…
					</p>
					<p v-else-if="document.status === 'failed'" class="text-xs text-red-600 truncate" :title="document.error">{{ document.error }}</p>
					<p v-else class="text-xs text-slate-400">{{ describe(document) }}</p>
				</div>
				<button
					class="w-7 h-7 rounded-md flex-center text-slate-400 opacity-0 group-hover:opacity-100 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/40 transition-300 cursor-pointer"
					title="Delete"
					@click="remove(document)"
				>
					<Icon name="lucide:trash-2" size="15" />
				</button>
			</li>
		</ul>
	</section>
</template>

<script lang="ts" setup>
import type { DocumentItem } from '~/types'

const store = useDocumentsStore()

const icons: Record<string, string> = {
	'application/pdf': 'lucide:file-text',
	'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'lucide:file-type',
	'text/markdown': 'lucide:file-code',
	'text/plain': 'lucide:file'
}

const dropZone = ref<HTMLElement>()
const { isOverDropZone } = useDropZone(dropZone, { onDrop: (files) => files && store.upload(files) })

function onPick(event: Event) {
	const input = event.target as HTMLInputElement
	if (input.files?.length) store.upload([...input.files])
	input.value = ''
}

// Documents are read in the background; check again until none is left in "processing"
const { pause, resume } = useIntervalFn(() => store.load(), 2000, { immediate: false })
watch(
	() => store.hasProcessing,
	(value) => (value ? resume() : pause()),
	{ immediate: true }
)

function describe(document: DocumentItem) {
	const size = document.size > 1024 * 1024 ? `${(document.size / 1024 / 1024).toFixed(1)} MB` : `${Math.ceil(document.size / 1024)} KB`
	return [document.pages ? `${document.pages} pages` : null, size].filter(Boolean).join(' · ')
}

async function remove(document: DocumentItem) {
	if (confirm(`Delete "${document.title}"?`)) await store.remove(document.id)
}
</script>
