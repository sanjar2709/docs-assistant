export default defineNuxtRouteMiddleware(async (to) => {
	const auth = useAuthStore()
	const isGuestPage = to.meta.layout === 'auth'

	if (!auth.isLoggedIn) {
		return isGuestPage ? undefined : navigateTo('/login')
	}
	if (isGuestPage) {
		return navigateTo('/')
	}
	if (!auth.user) {
		try {
			await auth.fetchMe()
		} catch {
			auth.logout()
		}
	}
})
