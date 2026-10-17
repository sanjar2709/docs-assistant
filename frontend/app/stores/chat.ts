import { defineStore } from 'pinia'

import type { ChatMessage, Conversation, ConversationDetail } from '~/types'

export const useChatStore = defineStore('chatStore', {
	state: () => ({
		conversations: [] as Conversation[],
		current: null as ConversationDetail | null,
		answering: false,
		error: ''
	}),

	actions: {
		async loadConversations() {
			const { $get } = useApi()
			this.conversations = await $get<Conversation[]>('conversations')
		},

		async open(id: number) {
			const { $get } = useApi()
			this.current = await $get<ConversationDetail>(`conversations/${id}`)
		},

		async create() {
			const { $post } = useApi()
			this.current = await $post<ConversationDetail>('conversations')
			this.conversations.unshift(this.current)
			return this.current
		},

		async remove(id: number) {
			const { $delete } = useApi()
			await $delete(`conversations/${id}`)
			this.conversations = this.conversations.filter((c) => c.id !== id)
			if (this.current?.id === id) this.current = null
		},

		/** Sends a question and fills in the answer as it streams in. */
		async ask(question: string) {
			const conversation = this.current ?? (await this.create())
			const now = new Date().toISOString()
			conversation.messages.push({ id: -Date.now(), role: 'user', content: question, citations: [], created_at: now })
			const answer: ChatMessage = { id: 0, role: 'assistant', content: '', citations: [], created_at: now }
			conversation.messages.push(answer)
			// Work on the reactive copy, so every streamed piece shows up right away
			const live = conversation.messages[conversation.messages.length - 1]!

			this.answering = true
			this.error = ''
			try {
				await streamAnswer(conversation.id, question, {
					text: (piece) => (live.content += piece),
					citation: (citation) => live.citations.push(citation),
					done: ({ message_id }) => (live.id = message_id)
				})
				if (conversation.title === 'New chat') {
					conversation.title = question.slice(0, 80)
					const item = this.conversations.find((c) => c.id === conversation.id)
					if (item) item.title = conversation.title
				}
			} catch (e) {
				this.error = errorMessage(e, 'The answer could not be loaded, please try again')
				conversation.messages.splice(-2)
			} finally {
				this.answering = false
			}
		}
	}
})
