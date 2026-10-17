<template>
	<span
		:title="name"
		:class="[sizes[size], colors[colorIndex]]"
		class="inline-flex items-center justify-center rounded-full font-semibold text-white uppercase shrink-0 ring-2 ring-white dark:ring-slate-900"
	>
		{{ initials }}
	</span>
</template>

<script lang="ts" setup>
interface Props {
	name: string
	size?: 'small' | 'medium'
}
const props = withDefaults(defineProps<Props>(), {
	size: 'medium'
})

const sizes = { small: 'w-6 h-6 text-[10px]', medium: 'w-8 h-8 text-xs' }
const colors = ['bg-rose-500', 'bg-amber-500', 'bg-emerald-500', 'bg-sky-500', 'bg-violet-500', 'bg-fuchsia-500', 'bg-teal-500']

const initials = computed(() =>
	props.name
		.split(/[\s@.]+/)
		.filter(Boolean)
		.slice(0, 2)
		.map((part) => part[0])
		.join('')
)
// Same person always gets the same color
const colorIndex = computed(() => [...props.name].reduce((sum, char) => sum + char.charCodeAt(0), 0) % colors.length)
</script>
