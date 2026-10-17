import { defineStore } from 'pinia'

import type { TokenPair, User } from '~/types'

const cookieOptions = { sameSite: 'lax' as const, maxAge: 60 * 60 * 24 * 7 }

export const useAuthStore = defineStore('authStore', {
	state: () => ({
		user: null as User | null,
		access: useCookie<string | null>('access_token', cookieOptions),
		refresh: useCookie<string | null>('refresh_token', cookieOptions)
	}),

	getters: {
		isLoggedIn: (state) => !!state.access
	},

	actions: {
		setTokens(tokens: TokenPair) {
			this.access = tokens.access
			this.refresh = tokens.refresh
		},

		async login(email: string, password: string) {
			const { $post } = useApi()
			this.setTokens(await $post<TokenPair>('auth/login', { body: { email, password } }))
			await this.fetchMe()
		},

		async register(payload: { email: string; password: string; full_name: string }) {
			const { $post } = useApi()
			await $post('auth/register', { body: payload })
			await this.login(payload.email, payload.password)
		},

		async fetchMe() {
			const { $get } = useApi()
			this.user = await $get<User>('auth/me')
		},

		/** Returns false when the refresh token is gone or expired, then the user has to log in again. */
		async refreshTokens(): Promise<boolean> {
			if (!this.refresh) return false
			try {
				const tokens = await $fetch<TokenPair>('auth/refresh', {
					baseURL: useRuntimeConfig().public.apiBaseUrl,
					method: 'POST',
					body: { refresh: this.refresh }
				})
				this.setTokens(tokens)
				return true
			} catch {
				return false
			}
		},

		logout() {
			this.user = null
			this.access = null
			this.refresh = null
			navigateTo('/login')
		}
	}
})
