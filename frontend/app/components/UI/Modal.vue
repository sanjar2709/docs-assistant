<template>
	<Teleport to="body">
		<Transition name="modal">
			<div
				v-if="show"
				class="fixed inset-0 z-[100] flex items-start sm:items-center justify-center bg-slate-950/60 backdrop-blur-sm p-3 overflow-y-auto"
				@mousedown.self="emit('close')"
			>
				<div class="w-full bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 my-8" :class="bodyClass">
					<div class="flex items-center justify-between gap-4 px-5 py-4 border-b border-slate-100 dark:border-slate-800">
						<slot name="header">
							<h3 class="text-lg font-semibold">{{ title }}</h3>
						</slot>
						<button
							class="w-8 h-8 rounded-lg flex-center text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 transition-300 cursor-pointer"
							@click="emit('close')"
						>
							<Icon name="lucide:x" />
						</button>
					</div>
					<div class="p-5">
						<slot />
					</div>
				</div>
			</div>
		</Transition>
	</Teleport>
</template>

<script lang="ts" setup>
interface Props {
	show?: boolean
	title?: string
	bodyClass?: string
}
const props = withDefaults(defineProps<Props>(), {
	show: false,
	title: '',
	bodyClass: 'max-w-[480px]'
})

const emit = defineEmits<{ close: [] }>()

onKeyStroke('Escape', () => props.show && emit('close'))
</script>
