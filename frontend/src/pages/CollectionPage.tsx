import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import {
  deleteDocument,
  listDocuments,
  uploadDocument,
} from '../lib/documents'

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function CollectionPage() {
  const { id } = useParams<{ id: string }>()
  const collectionId = Number(id)
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)

  const { data: documents, isLoading } = useQuery({
    queryKey: ['documents', collectionId],
    queryFn: () => listDocuments(collectionId),
    refetchInterval: (query) => {
      const stillProcessing = query.state.data?.some(
        (doc) => doc.status === 'uploaded' || doc.status === 'processing',
      )
      return stillProcessing ? 1500 : false
    },
  })

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadDocument(collectionId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', collectionId] })
      setUploadError(null)
    },
    onError: (err: Error) => setUploadError(err.message),
  })

  const deleteMutation = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', collectionId] })
    },
  })

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) uploadMutation.mutate(file)
    e.target.value = ''
  }

  return (
    <div className="min-h-screen bg-white">
      <header className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
        <Link to="/" className="text-sm text-gray-500 hover:underline">
          ← Collections
        </Link>
      </header>

      <main className="max-w-2xl mx-auto px-6 py-10 space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-semibold text-gray-900">Documents</h1>
          <div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.txt,.md"
              className="hidden"
              onChange={handleFileChange}
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploadMutation.isPending}
              className="bg-gray-900 text-white rounded px-4 py-2 text-sm disabled:opacity-50"
            >
              {uploadMutation.isPending ? 'Uploading…' : 'Upload document'}
            </button>
          </div>
        </div>
        {uploadError && <p className="text-sm text-red-600">{uploadError}</p>}

        {isLoading && <p className="text-sm text-gray-500">Loading…</p>}

        <ul className="divide-y divide-gray-200 border border-gray-200 rounded-lg">
          {documents?.map((doc) => (
            <li
              key={doc.id}
              className="flex items-center justify-between px-4 py-3"
            >
              <div className="text-sm">
                <p className="text-gray-900">{doc.filename}</p>
                <p className="text-gray-500">
                  {formatSize(doc.size_bytes)} · {doc.status}
                </p>
              </div>
              <button
                onClick={() => deleteMutation.mutate(doc.id)}
                className="text-sm text-red-600"
              >
                Delete
              </button>
            </li>
          ))}
          {documents?.length === 0 && (
            <li className="px-4 py-6 text-sm text-gray-500 text-center">
              No documents yet.
            </li>
          )}
        </ul>
      </main>
    </div>
  )
}
