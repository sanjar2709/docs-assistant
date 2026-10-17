<template>
	<header class="h-14 shrink-0 border-b border-slate-200 bg-white/80 backdrop-blur dark:border-slate-800 dark:bg-slate-900/80 sticky top-0 z-30">
		<div class="container h-full flex items-center justify-between gap-4">
			<NuxtLink to="/" class="flex items-center gap-2 font-bold text-lg">
				<img src="/favicon.svg" alt="" class="w-7 h-7" />
				<span>Docs Assistant</span>
			</NuxtLink>

			<div class="flex items-center gap-2">
				<button
					class="w-9 h-9 rounded-lg flex-center text-slate-500 hover:bg-slate-100 hover:text-slate-800 dark:hover:bg-slate-800 dark:hover:text-slate-100 transition-300 cursor-pointer"
					:title="isDark ? 'Light mode' : 'Dark mode'"
					@click="toggleDark()"
				>
					<Icon :name="isDark ? 'lucide:sun' : 'lucide:moon'" />
				</button>

				<div v-if="auth.user" ref="menuRef" class="relative">
					<button class="flex items-center gap-2 rounded-lg pl-1 pr-2 h-9 hover:bg-slate-100 dark:hover:bg-slate-800 transition-300 cursor-pointer" @click="showMenu = !showMenu">
						<UIAvatar :name="displayName" />
						<span class="hidden sm:block text-sm font-medium max-w-[160px] truncate">{{ displayName }}</span>
						<Icon name="lucide:chevron-down" size="16" class="text-slate-400" />
					</button>
					<Transition name="modal">
						<div v-if="showMenu" class="absolute right-0 mt-2 w-56 rounded-xl border border-slate-200 bg-white p-1.5 shadow-lg dark:border-slate-800 dark:bg-slate-900">
							<p class="px-3 py-2 text-xs text-slate-500 truncate">{{ auth.user.email }}</p>
							<button
								class="w-full flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-950/40 transition-300 cursor-pointer"
								@click="auth.logout()"
							>
								<Icon name="lucide:log-out" size="16" />
								Log out
							</button>
						</div>
					</Transition>
				</div>
			</div>
		</div>
	</header>
</template>

<script lang="ts" setup>
const auth = useAuthStore()
const isDark = useDark()
const toggleDark = useToggle(isDark)

const showMenu = ref(false)
const menuRef = ref<HTMLElement>()
onClickOutside(menuRef, () => (showMenu.value = false))

const displayName = computed(() => auth.user?.full_name || auth.user?.email || '')
</script>
