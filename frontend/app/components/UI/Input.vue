<template>
	<label class="block">
		<span v-if="label" class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">{{ label }}</span>
		<textarea
			v-if="multiline"
			v-model="model"
			v-bind="$attrs"
			rows="4"
			class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none transition-300 placeholder:text-slate-400 focus:border-primary-500 focus:ring-4 focus:ring-primary-500/15 dark:border-slate-700 dark:bg-slate-950 resize-y min-h-24"
		/>
		<input
			v-else
			v-model="model"
			v-bind="$attrs"
			:type="type"
			class="w-full h-10 rounded-lg border border-slate-200 bg-white px-3 text-sm outline-none transition-300 placeholder:text-slate-400 focus:border-primary-500 focus:ring-4 focus:ring-primary-500/15 dark:border-slate-700 dark:bg-slate-950"
		/>
	</label>
</template>

<script lang="ts" setup>
defineOptions({ inheritAttrs: false })

interface Props {
	label?: string
	type?: string
	multiline?: boolean
}
withDefaults(defineProps<Props>(), {
	label: '',
	type: 'text',
	multiline: false
})

const model = defineModel<string>({ default: '' })
</script>
