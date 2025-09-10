import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getSocket } from '../lib/socket'

export function Home() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [joinCode, setJoinCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const socket = getSocket()

  function ensureUsername(): string | null {
    const name = username.trim()
    if (!name) {
      setError('Please enter a username')
      return null
    }
    return name
  }

  const handleCreate = () => {
    const name = ensureUsername()
    if (!name) return
    setLoading(true)
    setError(null)
    socket.emit('create_room', { username: name })
    socket.once('room_created', ({ room_id }: { room_id: string }) => {
      navigate(`/room/${room_id}`, { state: { username: name, admin: true } })
    })
    socket.once('error', (e: any) => setError(e?.message || 'Error creating room'))
    setLoading(false)
  }

  const handleJoin = () => {
    const name = ensureUsername()
    if (!name) return
    const code = joinCode.trim()
    if (!code) {
      setError('Enter a room code to join')
      return
    }
    setLoading(true)
    setError(null)
    socket.emit('join_room', { room_id: code, username: name })
    socket.once('joined_room', ({ room_id }: { room_id: string }) => {
      navigate(`/room/${room_id}`, { state: { username: name } })
    })
    socket.once('error', (e: any) => setError(e?.message || 'Error joining room'))
    setLoading(false)
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-xl shadow p-6 space-y-5">
        <h1 className="text-2xl font-semibold text-center">Talk Caves</h1>
        <div className="space-y-2">
          <label className="text-sm font-medium">Username</label>
          <input
            className="w-full border rounded-lg px-3 py-2 focus:outline-none focus:ring focus:ring-indigo-200"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Enter your name"
          />
        </div>
        <button
          onClick={handleCreate}
          disabled={loading}
          className="w-full bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
        >
          Create New Room
        </button>

        <div className="relative flex items-center justify-center">
          <div className="absolute inset-x-0 border-t" />
          <span className="bg-white px-2 text-xs text-gray-500">or</span>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Join by Room Code</label>
          <div className="flex gap-2">
            <input
              className="flex-1 border rounded-lg px-3 py-2 focus:outline-none focus:ring focus:ring-indigo-200"
              value={joinCode}
              onChange={(e) => setJoinCode(e.target.value)}
              placeholder="e.g. 4f2a9c1b"
            />
            <button
              onClick={handleJoin}
              disabled={loading}
              className="bg-gray-900 text-white px-4 py-2 rounded-lg hover:bg-black disabled:opacity-50"
            >
              Join
            </button>
          </div>
        </div>

        {error && <div className="text-sm text-red-600">{error}</div>}
        <p className="text-xs text-gray-500 text-center">Works great on mobile, too.</p>
      </div>
    </div>
  )
}


