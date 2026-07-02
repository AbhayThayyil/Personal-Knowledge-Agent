import { apiFetch } from './api'

export interface Document {
  id: number
  filename: string
  content_type: string
  size_bytes: number
  status: string
  collection_id: number
  uploaded_at: string
}

export function listDocuments(collectionId: number) {
  return apiFetch<Document[]>(`/documents?collection_id=${collectionId}`)
}

export function uploadDocument(collectionId: number, file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return apiFetch<Document>(`/documents/upload?collection_id=${collectionId}`, {
    method: 'POST',
    body: formData,
  })
}

export function deleteDocument(id: number) {
  return apiFetch<void>(`/documents/${id}`, { method: 'DELETE' })
}
