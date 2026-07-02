import { useEffect, useState } from 'react'

function App() {
  const [status, setStatus] = useState<'checking' | 'ok' | 'down'>('checking')

  useEffect(() => {
    fetch('/api/health')
      .then((res) => (res.ok ? res.json() : Promise.reject()))
      .then(() => setStatus('ok'))
      .catch(() => setStatus('down'))
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center bg-white">
      <div className="text-center space-y-2">
        <h1 className="text-2xl font-semibold text-gray-900">
          Personal Knowledge Agent
        </h1>
        <p className="text-sm text-gray-500">
          Backend status:{' '}
          <span
            className={
              status === 'ok'
                ? 'text-green-600'
                : status === 'down'
                  ? 'text-red-600'
                  : 'text-gray-400'
            }
          >
            {status}
          </span>
        </p>
      </div>
    </div>
  )
}

export default App
