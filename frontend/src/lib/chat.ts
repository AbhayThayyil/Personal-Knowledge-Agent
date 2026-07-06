import { useAuthStore } from '../store/authStore'
import { ApiError } from './api'

export interface Citation {
  filename: string
  page: number
}

interface StreamChatOptions {
  collectionId: number
  chatId: number | null
  message: string
  onStart: (chatId: number) => void
  onToken: (content: string) => void
  onDone: (citations: Citation[]) => void
}

export async function streamChat({
  collectionId,
  chatId,
  message,
  onStart,
  onToken,
  onDone,
}: StreamChatOptions): Promise<void> {
  const token = useAuthStore.getState().token

  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ collection_id: collectionId, chat_id: chatId, message }),
  })

  if (!res.ok || !res.body) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new ApiError(res.status, body.detail ?? 'Request failed')
  }

  // The browser's native EventSource API can't send an Authorization header,
  // so we read the SSE stream manually via fetch instead.
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const events = buffer.split('\n\n')
    buffer = events.pop() ?? ''

    for (const event of events) {
      const line = event.trim()
      if (!line.startsWith('data: ')) continue
      const payload = JSON.parse(line.slice('data: '.length))

      if (payload.type === 'start') {
        onStart(payload.chat_id)
      } else if (payload.type === 'token') {
        onToken(payload.content)
      } else if (payload.type === 'done') {
        onDone(payload.citations)
      }
    }
  }
}
