import { io, Socket } from 'socket.io-client'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

let socket: Socket | null = null

export function getSocket(): Socket {
  if (!socket) {
    socket = io(API_BASE, { transports: ['websocket'], autoConnect: true })
  }
  return socket
}


