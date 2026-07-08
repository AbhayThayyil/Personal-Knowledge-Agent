import { apiFetch } from './api'
import type { Citation } from './chat'

export interface ChatSummary {
  id: number
  title: string
  collection_id: number
  created_at: string
}

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  citations: Citation[]
  created_at: string
}

export interface ChatDetail extends ChatSummary {
  messages: ChatMessage[]
}

export function listChats(collectionId: number) {
  return apiFetch<ChatSummary[]>(`/chats?collection_id=${collectionId}`)
}

export function getChat(chatId: number) {
  return apiFetch<ChatDetail>(`/chats/${chatId}`)
}

export function renameChat(chatId: number, title: string) {
  return apiFetch<ChatSummary>(`/chats/${chatId}`, {
    method: 'PATCH',
    body: JSON.stringify({ title }),
  })
}

export function deleteChat(chatId: number) {
  return apiFetch<void>(`/chats/${chatId}`, { method: 'DELETE' })
}
