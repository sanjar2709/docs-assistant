<template>
	<div>
		<h1 class="text-xl font-bold mb-1">Create an account</h1>
		<p class="text-sm text-slate-500 mb-6">It takes half a minute</p>

		<form class="space-y-4" @submit.prevent="submit">
			<UIInput v-model="form.full_name" label="Name" autocomplete="name" />
			<UIInput v-model="form.email" label="Email" type="email" autocomplete="email" required />
			<UIInput v-model="form.password" label="Password" type="password" autocomplete="new-password" minlength="8" required />
			<UIAlert :text="error" />
			<UIButton type="submit" text="Sign up" class="w-full" :loading="loading" />
		</form>

		<p class="text-sm text-center text-slate-500 mt-6">
			Already have an account?
			<NuxtLink to="/login" class="font-semibold text-primary-600 hover:underline">Log in</NuxtLink>
		</p>
	</div>
</template>

<script lang="ts" setup>
definePageMeta({ layout: 'auth' })
useHead({ title: 'Sign up' })

const auth = useAuthStore()

const form = reactive({ full_name: '', email: '', password: '' })
const loading = ref(false)
const error = ref('')

async function submit() {
	loading.value = true
	error.value = ''
	try {
		await auth.register(form)
		await navigateTo('/')
	} catch (e) {
		error.value = errorMessage(e)
	} finally {
		loading.value = false
	}
}
</script>
