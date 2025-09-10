import { useEffect, useMemo, useRef, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { getSocket } from '../lib/socket'

type Message = {
  username: string
  content: string
  timestamp: string
}

export function Room() {
  const { roomId } = useParams()
  const { state } = useLocation() as { state?: { username?: string } }
  const navigate = useNavigate()
  const socket = getSocket()

  const username = state?.username || 'Guest'
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [typingUser, setTypingUser] = useState<string | null>(null)
  const [usersCount, setUsersCount] = useState<number>(1)

  const listRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!roomId) return

    const onMessage = (msg: any) => {
      if (msg.room_id !== roomId) return
      setMessages((m) => [...m, { username: msg.username, content: msg.content, timestamp: msg.timestamp }])
    }
    const onUserJoined = (p: any) => {
      if (p.room_id !== roomId) return
      setUsersCount(p.users_count)
      setMessages((m) => [...m, { username: 'system', content: `${p.username} joined`, timestamp: new Date().toISOString() }])
    }
    const onUserLeft = (p: any) => {
      if (p.room_id !== roomId) return
      setUsersCount(p.users_count)
      setMessages((m) => [...m, { username: 'system', content: `${p.username} left`, timestamp: new Date().toISOString() }])
    }
    const onTyping = (p: any) => {
      if (p.room_id !== roomId) return
      setTypingUser(p.is_typing ? p.username : null)
    }
    const onRoomClosed = (p: any) => {
      if (p.room_id !== roomId) return
      alert('Room was closed')
      navigate('/')
    }

    socket.on('message', onMessage)
    socket.on('user_joined', onUserJoined)
    socket.on('user_left', onUserLeft)
    socket.on('typing', onTyping)
    socket.on('room_closed', onRoomClosed)

    return () => {
      socket.off('message', onMessage)
      socket.off('user_joined', onUserJoined)
      socket.off('user_left', onUserLeft)
      socket.off('typing', onTyping)
      socket.off('room_closed', onRoomClosed)
    }
  }, [roomId, socket, navigate])

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight })
  }, [messages.length])

  const sendMessage = () => {
    const text = input.trim()
    if (!text || !roomId) return
    socket.emit('message', { room_id: roomId, content: text })
    setInput('')
  }

  const onInputChange = (v: string) => {
    setInput(v)
    if (!roomId) return
    socket.emit('typing', { room_id: roomId, is_typing: v.length > 0 })
  }

  const leave = () => {
    socket.emit('leave_room')
    navigate('/')
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="flex items-center justify-between px-4 py-3 border-b bg-white">
        <div>
          <div className="font-semibold">Room {roomId}</div>
          <div className="text-xs text-gray-500">Users: {usersCount}</div>
        </div>
        <button onClick={leave} className="text-sm px-3 py-1.5 rounded-lg bg-gray-900 text-white">Leave</button>
      </header>

      <div ref={listRef} className="flex-1 overflow-auto p-4 space-y-2">
        {messages.map((m, i) => (
          <div key={i} className={`max-w-[80%] ${m.username === username ? 'ml-auto text-right' : 'mr-auto'}`}>
            <div className="text-xs text-gray-500 mb-0.5">{m.username}</div>
            <div className="inline-block bg-white rounded-xl shadow px-3 py-2">{m.content}</div>
          </div>
        ))}
      </div>

      <div className="px-4 pb-4 space-y-2 bg-white border-t">
        {typingUser && <div className="text-xs text-gray-500">{typingUser} is typing…</div>}
        <div className="flex gap-2">
          <input
            className="flex-1 border rounded-lg px-3 py-2 focus:outline-none focus:ring focus:ring-indigo-200"
            value={input}
            onChange={(e) => onInputChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') sendMessage()
            }}
            placeholder="Type a message"
          />
          <button onClick={sendMessage} className="px-4 py-2 rounded-lg bg-indigo-600 text-white">Send</button>
        </div>
      </div>
    </div>
  )
}


