import React, { useEffect, useState } from 'react';
import { io, Socket } from 'socket.io-client';
import LiveFeedGrid from '../components/LiveFeedGrid';
import AlertPanel from '../components/AlertPanel';
import RiskHeatmap from '../components/RiskHeatmap';
import ZoneEditor from '../components/ZoneEditor';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Dashboard() {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [liveFrame, setLiveFrame] = useState(null);
  const [alerts, setAlerts] = useState<any[]>([]);

  useEffect(() => {
    // python-socketio ASGIApp is mounted at /ws
    // The socket.io client will append /socket.io automatically to the path if not specified
    // But since we mount the ASGI app at /ws, the actual socket.io endpoint is /ws/socket.io
    const newSocket = io(API_URL, {
      path: '/ws/socket.io' 
    });

    newSocket.on('connect', () => {
      console.log('Connected to WebSocket server');
    });

    newSocket.on('live_frame', (data) => {
      setLiveFrame(data);
    });

    newSocket.on('alert', (alert) => {
      setAlerts(prev => [alert, ...prev].slice(0, 50)); // Keep last 50 alerts
    });

    setSocket(newSocket);

    return () => {
      newSocket.close();
    };
  }, []);

  return (
    <div className="min-h-screen bg-slate-900 p-6">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
          AI Safety Dashboard
        </h1>
        <p className="text-slate-400 mt-1">Real-time Unsafe Human Activity Detection</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <LiveFeedGrid liveFrame={liveFrame} />
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <RiskHeatmap />
            <ZoneEditor />
          </div>
        </div>
        
        <div className="lg:col-span-1">
          <AlertPanel alerts={alerts} />
        </div>
      </div>
    </div>
  );
}
