import type { FetchOptions } from 'ofetch'

export const useApi = () => {
	const config = useRuntimeConfig()
	const auth = useAuthStore()
	const loading = ref(false)

	function $service(options?: FetchOptions) {
		return $fetch.create({
			...options,
			baseURL: config.public.apiBaseUrl,
			headers: {
				...options?.headers,
				...(auth.access ? { Authorization: `Bearer ${auth.access}` } : {})
			}
		})
	}

	async function request<T>(endpoint: string, options?: FetchOptions): Promise<T> {
		loading.value = true
		try {
			return (await $service(options)<T>(endpoint)) as T
		} catch (error) {
			// Access token lives 30 minutes: on 401 get a new pair once and repeat the request
			if ((error as { status?: number }).status === 401 && auth.refresh && !endpoint.startsWith('auth/')) {
				if (await auth.refreshTokens()) {
					return (await $service(options)<T>(endpoint)) as T
				}
				auth.logout()
			}
			throw error
		} finally {
			loading.value = false
		}
	}

	const $get = <T = never>(endpoint: string, options?: FetchOptions) => request<T>(endpoint, { ...options, method: 'GET' })
	const $post = <T = never>(endpoint: string, options?: FetchOptions) => request<T>(endpoint, { ...options, method: 'POST' })
	const $patch = <T = never>(endpoint: string, options?: FetchOptions) => request<T>(endpoint, { ...options, method: 'PATCH' })
	const $delete = <T = never>(endpoint: string, options?: FetchOptions) => request<T>(endpoint, { ...options, method: 'DELETE' })

	return { loading, $get, $post, $patch, $delete }
}
