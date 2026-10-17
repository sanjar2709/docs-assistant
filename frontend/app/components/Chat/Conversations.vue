<template>
	<section class="flex flex-col min-h-0">
		<div class="flex items-center justify-between mb-3">
			<h2 class="text-sm font-semibold text-slate-500 uppercase tracking-wide">Chats</h2>
			<button class="inline-flex items-center gap-1 text-xs font-semibold text-primary-600 hover:underline cursor-pointer" @click="store.current = null">
				<Icon name="lucide:plus" size="14" /> New
			</button>
		</div>
		<p v-if="!store.conversations.length" class="text-xs text-slate-400">Your questions will be saved here.</p>
		<ul class="space-y-1 overflow-y-auto scroll-thin min-h-0">
			<li v-for="conversation in store.conversations" :key="conversation.id">
				<button
					class="group w-full flex items-center gap-2 rounded-lg px-2.5 py-2 text-left text-sm transition-300 cursor-pointer"
					:class="
						conversation.id === store.current?.id ? 'bg-primary-50 text-primary-700 dark:bg-primary-600/15 dark:text-primary-100' : 'hover:bg-slate-100 dark:hover:bg-slate-800/60'
					"
					@click="store.open(conversation.id)"
				>
					<Icon name="lucide:message-square" size="15" class="shrink-0 opacity-60" />
					<span class="flex-1 truncate">{{ conversation.title }}</span>
					<Icon name="lucide:x" size="14" class="opacity-0 group-hover:opacity-60 hover:!opacity-100" @click.stop="store.remove(conversation.id)" />
				</button>
			</li>
		</ul>
	</section>
</template>

<script lang="ts" setup>
const store = useChatStore()
</script>
