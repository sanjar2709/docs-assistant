import type { Citation } from '~/types'

interface Handlers {
	text: (piece: string) => void
	citation: (citation: Citation) => void
	done: (data: { message_id: number; conversation_id: number }) => void
}

/**
 * POSTs a question and reads the server-sent events of the answer.
 * EventSource can only do GET without a body, so this reads the response stream by hand.
 */
export async function streamAnswer(conversationId: number, question: string, handlers: Handlers) {
	const config = useRuntimeConfig()
	const auth = useAuthStore()

	const send = () =>
		fetch(`${config.public.apiBaseUrl}conversations/${conversationId}/messages`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${auth.access}` },
			body: JSON.stringify({ question })
		})

	let response = await send()
	if (response.status === 401 && (await auth.refreshTokens())) {
		response = await send()
	}
	if (!response.ok || !response.body) {
		throw { data: await response.json().catch(() => null) }
	}

	const reader = response.body.pipeThrough(new TextDecoderStream()).getReader()
	let buffer = ''
	while (true) {
		const { value, done } = await reader.read()
		if (done) break
		buffer += value
		// Events are separated by a blank line; the last piece may still be incomplete
		const blocks = buffer.split('\n\n')
		buffer = blocks.pop() ?? ''
		for (const block of blocks) {
			const event = block.match(/^event: (.+)$/m)?.[1]
			const data = block.match(/^data: (.+)$/m)?.[1]
			if (!event || !data) continue
			const payload = JSON.parse(data)
			if (event === 'text') handlers.text(payload.text)
			else if (event === 'citation') handlers.citation(payload)
			else if (event === 'done') handlers.done(payload)
		}
	}
}
