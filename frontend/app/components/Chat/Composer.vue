<template>
	<form class="relative" @submit.prevent="send">
		<textarea
			ref="input"
			v-model="question"
			rows="1"
			maxlength="2000"
			:placeholder="placeholder"
			:disabled="disabled"
			class="w-full resize-none rounded-2xl border border-slate-200 bg-white pl-4 pr-14 py-3.5 text-[15px] outline-none shadow-sm transition-300 focus:border-primary-500 focus:ring-4 focus:ring-primary-500/15 disabled:opacity-60 dark:border-slate-700 dark:bg-slate-900 max-h-40"
			@keydown.enter.exact.prevent="send"
			@input="grow"
		/>
		<button
			type="submit"
			:disabled="disabled || !question.trim()"
			class="absolute right-2.5 bottom-2.5 w-9 h-9 rounded-xl flex-center bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-40 transition-300 cursor-pointer"
			title="Send"
		>
			<Icon name="lucide:arrow-up" size="18" />
		</button>
	</form>
</template>

<script lang="ts" setup>
interface Props {
	disabled?: boolean
	placeholder?: string
}
withDefaults(defineProps<Props>(), {
	disabled: false,
	placeholder: 'Ask about your documents…'
})

const emit = defineEmits<{ send: [question: string] }>()

const question = ref('')
const input = ref<HTMLTextAreaElement>()

function grow() {
	if (!input.value) return
	input.value.style.height = 'auto'
	input.value.style.height = `${input.value.scrollHeight}px`
}

function send() {
	const value = question.value.trim()
	if (!value) return
	emit('send', value)
	question.value = ''
	nextTick(grow)
}

defineExpose({ focus: () => input.value?.focus() })
</script>
