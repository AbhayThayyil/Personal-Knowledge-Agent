import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import { Link, useParams } from 'react-router-dom'
import { ApiError } from '../lib/api'
import { streamChat } from '../lib/chat'
import type { Citation } from '../lib/chat'
import {
  deleteChat,
  getChat,
  listChats,
  renameChat,
} from '../lib/chats'

interface Message {
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
}

export default function ChatPage() {
  const { id } = useParams<{ id: string }>()
  const collectionId = Number(id)
  const queryClient = useQueryClient()

  const [activeChatId, setActiveChatId] = useState<number | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const { data: chats } = useQuery({
    queryKey: ['chats', collectionId],
    queryFn: () => listChats(collectionId),
  })

  const deleteMutation = useMutation({
    mutationFn: deleteChat,
    onSuccess: (_data, deletedId) => {
      queryClient.invalidateQueries({ queryKey: ['chats', collectionId] })
      if (activeChatId === deletedId) handleNewChat()
    },
  })

  const renameMutation = useMutation({
    mutationFn: ({ chatId, title }: { chatId: number; title: string }) =>
      renameChat(chatId, title),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chats', collectionId] })
    },
  })

  function handleNewChat() {
    setActiveChatId(null)
    setMessages([])
    setError(null)
  }

  async function handleSelectChat(chatId: number) {
    setError(null)
    const chat = await getChat(chatId)
    setActiveChatId(chat.id)
    setMessages(
      chat.messages.map((m) => ({
        role: m.role,
        content: m.content,
        citations: m.citations,
      })),
    )
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const question = input.trim()
    if (!question || isStreaming) return

    setError(null)
    setInput('')
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: question },
      { role: 'assistant', content: '' },
    ])
    setIsStreaming(true)

    try {
      await streamChat({
        collectionId,
        chatId: activeChatId,
        message: question,
        onStart: (chatId) => {
          const isNewChat = activeChatId === null
          setActiveChatId(chatId)
          if (isNewChat) {
            queryClient.invalidateQueries({ queryKey: ['chats', collectionId] })
          }
        },
        onToken: (content) => {
          setMessages((prev) => {
            const updated = [...prev]
            const last = updated[updated.length - 1]
            updated[updated.length - 1] = { ...last, content: last.content + content }
            return updated
          })
        },
        onDone: (citations) => {
          setMessages((prev) => {
            const updated = [...prev]
            const last = updated[updated.length - 1]
            updated[updated.length - 1] = { ...last, citations }
            return updated
          })
        },
      })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong')
    } finally {
      setIsStreaming(false)
    }
  }

  return (
    <div className="min-h-screen bg-white flex">
      <aside className="w-56 border-r border-gray-200 flex flex-col">
        <div className="px-4 py-4 border-b border-gray-200">
          <Link
            to={`/collections/${collectionId}`}
            className="text-sm text-gray-500 hover:underline"
          >
            ← Back to documents
          </Link>
        </div>
        <button
          onClick={handleNewChat}
          className="mx-4 mt-4 bg-gray-900 text-white rounded px-3 py-2 text-sm"
        >
          + New chat
        </button>
        <ul className="mt-4 flex-1 overflow-y-auto">
          {chats?.map((c) => (
            <li
              key={c.id}
              className={`group flex items-center justify-between px-4 py-2 text-sm cursor-pointer hover:bg-gray-50 ${
                activeChatId === c.id ? 'bg-gray-100' : ''
              }`}
            >
              <button
                onClick={() => handleSelectChat(c.id)}
                className="flex-1 text-left truncate text-gray-900"
              >
                {c.title}
              </button>
              <div className="hidden group-hover:flex gap-2 ml-2">
                <button
                  onClick={() => {
                    const title = window.prompt('Rename chat', c.title)
                    if (title) renameMutation.mutate({ chatId: c.id, title })
                  }}
                  className="text-xs text-gray-500"
                >
                  Rename
                </button>
                <button
                  onClick={() => deleteMutation.mutate(c.id)}
                  className="text-xs text-red-600"
                >
                  Delete
                </button>
              </div>
            </li>
          ))}
        </ul>
      </aside>

      <div className="flex-1 flex flex-col">
        <main className="flex-1 max-w-2xl w-full mx-auto px-6 py-8 flex flex-col gap-6 overflow-y-auto">
          {messages.length === 0 && (
            <p className="text-sm text-gray-500 text-center mt-10">
              Ask a question about the documents in this collection.
            </p>
          )}
          {messages.map((message, i) => (
            <div key={i} className={message.role === 'user' ? 'text-right' : ''}>
              <div
                className={
                  message.role === 'user'
                    ? 'inline-block bg-gray-900 text-white rounded-lg px-4 py-2 text-sm max-w-lg text-left'
                    : 'text-sm text-gray-900'
                }
              >
                {message.role === 'assistant' ? (
                  <ReactMarkdown>{message.content || '…'}</ReactMarkdown>
                ) : (
                  message.content
                )}
              </div>
              {message.citations && message.citations.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {message.citations.map((citation, j) => (
                    <span
                      key={j}
                      className="text-xs text-gray-500 border border-gray-200 rounded px-2 py-1"
                    >
                      {citation.filename} · page {citation.page}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </main>

        <form
          onSubmit={handleSubmit}
          className="border-t border-gray-200 px-6 py-4 max-w-2xl w-full mx-auto flex gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question…"
            disabled={isStreaming}
            className="flex-1 border border-gray-300 rounded px-3 py-2 text-sm disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isStreaming || !input.trim()}
            className="bg-gray-900 text-white rounded px-4 py-2 text-sm disabled:opacity-50"
          >
            {isStreaming ? 'Thinking…' : 'Send'}
          </button>
        </form>
        {error && <p className="text-sm text-red-600 text-center pb-4">{error}</p>}
      </div>
    </div>
  )
}
