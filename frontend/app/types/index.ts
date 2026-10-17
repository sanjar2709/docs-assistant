export interface User {
	id: number
	email: string
	full_name: string
	created_at: string
}

export interface TokenPair {
	access: string
	refresh: string
}

export type DocumentStatus = 'processing' | 'ready' | 'failed'

export interface DocumentItem {
	id: number
	title: string
	content_type: string
	size: number
	status: DocumentStatus
	error: string
	pages: number | null
	chunks_count: number
	created_at: string
}

export interface Citation {
	chunk_id: number
	document_id: number
	document_title: string
	page: number | null
	cited_text: string
}

export interface ChatMessage {
	id: number
	role: 'user' | 'assistant'
	content: string
	citations: Citation[]
	created_at: string
}

export interface Conversation {
	id: number
	title: string
	created_at: string
	updated_at: string
}

export interface ConversationDetail extends Conversation {
	messages: ChatMessage[]
}

export interface ApiError {
	error: {
		code: string
		message: string
		details: { field: string; message: string }[] | null
	}
}
