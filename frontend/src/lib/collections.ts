import { apiFetch } from './api'

export interface Collection {
  id: number
  name: string
  created_at: string
}

export function listCollections() {
  return apiFetch<Collection[]>('/collections')
}

export function createCollection(name: string) {
  return apiFetch<Collection>('/collections', {
    method: 'POST',
    body: JSON.stringify({ name }),
  })
}

export function renameCollection(id: number, name: string) {
  return apiFetch<Collection>(`/collections/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ name }),
  })
}

export function deleteCollection(id: number) {
  return apiFetch<void>(`/collections/${id}`, { method: 'DELETE' })
}
