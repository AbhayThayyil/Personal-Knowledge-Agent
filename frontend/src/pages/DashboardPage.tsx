import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { apiFetch } from '../lib/api'
import {
  createCollection,
  deleteCollection,
  listCollections,
} from '../lib/collections'
import { useAuthStore } from '../store/authStore'

export default function DashboardPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const user = useAuthStore((s) => s.user)
  const clearSession = useAuthStore((s) => s.clearSession)
  const [name, setName] = useState('')

  const { data: collections, isLoading } = useQuery({
    queryKey: ['collections'],
    queryFn: listCollections,
  })

  const createMutation = useMutation({
    mutationFn: createCollection,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] })
      setName('')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteCollection,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] })
    },
  })

  async function handleLogout() {
    await apiFetch('/auth/logout', { method: 'POST' }).catch(() => {})
    clearSession()
    navigate('/login')
  }

  function handleCreate(e: FormEvent) {
    e.preventDefault()
    if (name.trim()) createMutation.mutate(name.trim())
  }

  return (
    <div className="min-h-screen bg-white">
      <header className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
        <h1 className="text-lg font-semibold text-gray-900">
          Personal Knowledge Agent
        </h1>
        <div className="flex items-center gap-3 text-sm text-gray-500">
          <span>{user?.email}</span>
          <button onClick={handleLogout} className="underline">
            Log out
          </button>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-6 py-10 space-y-6">
        <form onSubmit={handleCreate} className="flex gap-2">
          <input
            type="text"
            placeholder="New collection name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="flex-1 border border-gray-300 rounded px-3 py-2 text-sm"
          />
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="bg-gray-900 text-white rounded px-4 py-2 text-sm disabled:opacity-50"
          >
            Create
          </button>
        </form>
        {createMutation.isError && (
          <p className="text-sm text-red-600">
            {(createMutation.error as Error).message}
          </p>
        )}

        {isLoading && <p className="text-sm text-gray-500">Loading…</p>}

        <ul className="divide-y divide-gray-200 border border-gray-200 rounded-lg">
          {collections?.map((collection) => (
            <li
              key={collection.id}
              className="flex items-center justify-between px-4 py-3"
            >
              <Link
                to={`/collections/${collection.id}`}
                className="text-sm text-gray-900 hover:underline"
              >
                {collection.name}
              </Link>
              <button
                onClick={() => deleteMutation.mutate(collection.id)}
                className="text-sm text-red-600"
              >
                Delete
              </button>
            </li>
          ))}
          {collections?.length === 0 && (
            <li className="px-4 py-6 text-sm text-gray-500 text-center">
              No collections yet.
            </li>
          )}
        </ul>
      </main>
    </div>
  )
}
