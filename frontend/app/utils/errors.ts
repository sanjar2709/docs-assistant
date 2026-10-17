import type { ApiError } from '~/types'

/** Turns an error from the API into text for the user. */
export function errorMessage(error: unknown, fallback = 'Something went wrong, please try again'): string {
	const data = (error as { data?: ApiError })?.data
	if (!data?.error) return fallback
	if (data.error.details?.length) {
		return data.error.details.map((d) => (d.field ? `${d.field}: ${d.message}` : d.message)).join('\n')
	}
	return data.error.message
}
