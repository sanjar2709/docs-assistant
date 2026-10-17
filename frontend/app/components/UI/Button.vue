<template>
	<button
		:class="[variants[variant], sizes[size], { '!pointer-events-none': loading }]"
		class="relative inline-flex items-center justify-center gap-2 whitespace-nowrap font-semibold rounded-lg transition-300 active:scale-[0.98] disabled:opacity-60 disabled:pointer-events-none cursor-pointer"
		v-bind="{ disabled, type }"
	>
		<span :class="{ 'opacity-0': loading }" class="inline-flex items-center gap-2">
			<Icon v-if="icon" :name="icon" />
			<slot>{{ text }}</slot>
		</span>
		<Icon v-if="loading" name="lucide:loader-circle" class="absolute animate-spin" />
	</button>
</template>

<script lang="ts" setup>
interface Props {
	variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
	size?: 'small' | 'medium'
	type?: 'button' | 'submit'
	text?: string
	icon?: string
	loading?: boolean
	disabled?: boolean
}
withDefaults(defineProps<Props>(), {
	variant: 'primary',
	size: 'medium',
	type: 'button',
	text: '',
	icon: '',
	loading: false,
	disabled: false
})

const variants = {
	primary: 'bg-primary-600 text-white hover:bg-primary-700 shadow-sm',
	secondary: 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50 dark:bg-slate-800 dark:text-slate-200 dark:border-slate-700 dark:hover:bg-slate-700',
	ghost: 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800',
	danger: 'bg-red-600 text-white hover:bg-red-700'
}
const sizes = {
	small: 'h-8 px-3 text-sm',
	medium: 'h-10 px-4 text-sm'
}
</script>
