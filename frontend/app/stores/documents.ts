import { defineStore } from 'pinia'

import type { DocumentItem } from '~/types'

export const useDocumentsStore = defineStore('documentsStore', {
	state: () => ({
		items: [] as DocumentItem[],
		uploading: false,
		error: ''
	}),

	getters: {
		ready: (state) => state.items.filter((d) => d.status === 'ready'),
		hasProcessing: (state) => state.items.some((d) => d.status === 'processing')
	},

	actions: {
		async load() {
			const { $get } = useApi()
			this.items = await $get<DocumentItem[]>('documents')
		},

		async upload(files: File[]) {
			const { $post } = useApi()
			this.uploading = true
			this.error = ''
			try {
				for (const file of files) {
					const body = new FormData()
					body.append('file', file)
					const document = await $post<DocumentItem>('documents', { body })
					this.items.unshift(document)
				}
			} catch (e) {
				this.error = errorMessage(e)
			} finally {
				this.uploading = false
			}
		},

		async remove(id: number) {
			const { $delete } = useApi()
			await $delete(`documents/${id}`)
			this.items = this.items.filter((d) => d.id !== id)
		}
	}
})
