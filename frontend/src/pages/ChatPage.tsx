import { useState } from 'react'
import type { FormEvent } from 'react'
import ReactMarkdown from 'react-markdown'
import { Link, useParams } from 'react-router-dom'
import { ApiError } from '../lib/api'
import { streamChat } from '../lib/chat'
import type { Citation } from '../lib/chat'

interface Message {
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
}

export default function ChatPage() {
  const { id } = useParams<{ id: string }>()
  const collectionId = Number(id)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)

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
        message: question,
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
    <div className="min-h-screen bg-white flex flex-col">
      <header className="border-b border-gray-200 px-6 py-4">
        <Link
          to={`/collections/${collectionId}`}
          className="text-sm text-gray-500 hover:underline"
        >
          ← Back to documents
        </Link>
      </header>

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
  )
}
