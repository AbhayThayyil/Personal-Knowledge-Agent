import { useNavigate } from 'react-router-dom'
import { apiFetch } from '../lib/api'
import { useAuthStore } from '../store/authStore'

export default function DashboardPage() {
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const clearSession = useAuthStore((s) => s.clearSession)

  async function handleLogout() {
    await apiFetch('/auth/logout', { method: 'POST' }).catch(() => {})
    clearSession()
    navigate('/login')
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-white">
      <div className="text-center space-y-3">
        <h1 className="text-2xl font-semibold text-gray-900">
          Personal Knowledge Agent
        </h1>
        <p className="text-sm text-gray-500">Logged in as {user?.email}</p>
        <button
          onClick={handleLogout}
          className="text-sm text-gray-900 underline"
        >
          Log out
        </button>
      </div>
    </div>
  )
}
