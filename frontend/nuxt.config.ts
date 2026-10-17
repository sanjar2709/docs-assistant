import tailwindcss from '@tailwindcss/vite'

export default defineNuxtConfig({
	compatibilityDate: '2025-07-15',
	devtools: { enabled: true },
	// Dashboard behind a login, nothing to index, so a plain SPA is enough
	ssr: false,

	app: {
		head: {
			title: 'Docs Assistant',
			titleTemplate: '%s · Docs Assistant',
			htmlAttrs: { lang: 'en' },
			link: [{ rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' }]
		}
	},

	css: ['~/assets/css/main.css'],

	modules: [
		'@vueuse/nuxt',
		[
			'@pinia/nuxt',
			{
				autoImports: ['defineStore', ['defineStore', 'definePiniaStore']]
			}
		],
		'@nuxt/icon',
		'@nuxt/eslint'
	],
	vite: {
		plugins: [tailwindcss()]
	},
	icon: {
		size: '20px',
		// SPA: put the icons we use straight into the client bundle instead of fetching them at runtime
		clientBundle: {
			scan: true
		},
		serverBundle: {
			collections: ['lucide']
		}
	},
	runtimeConfig: {
		public: {
			apiBaseUrl: 'http://localhost:8003/api/v1/'
		}
	}
})
