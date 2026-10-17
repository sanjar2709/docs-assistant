<template>
	<div>
		<h1 class="text-xl font-bold mb-1">Welcome back</h1>
		<p class="text-sm text-slate-500 mb-6">Log in to see your boards</p>

		<form class="space-y-4" @submit.prevent="submit">
			<UIInput v-model="form.email" label="Email" type="email" autocomplete="email" required />
			<UIInput v-model="form.password" label="Password" type="password" autocomplete="current-password" required />
			<UIAlert :text="error" />
			<UIButton type="submit" text="Log in" class="w-full" :loading="loading" />
		</form>

		<p class="text-sm text-center text-slate-500 mt-6">
			No account yet?
			<NuxtLink to="/register" class="font-semibold text-primary-600 hover:underline">Sign up</NuxtLink>
		</p>
	</div>
</template>

<script lang="ts" setup>
definePageMeta({ layout: 'auth' })
useHead({ title: 'Log in' })

const auth = useAuthStore()

const form = reactive({ email: '', password: '' })
const loading = ref(false)
const error = ref('')

async function submit() {
	loading.value = true
	error.value = ''
	try {
		await auth.login(form.email, form.password)
		await navigateTo('/')
	} catch (e) {
		error.value = errorMessage(e)
	} finally {
		loading.value = false
	}
}
</script>
