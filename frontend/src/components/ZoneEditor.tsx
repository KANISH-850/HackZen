import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Point {
  x: number;
  y: number;
}

interface Zone {
  id?: number;
  name: string;
  polygon: Point[];
  risk_level: string;
}

export default function ZoneEditor() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [cameraId, setCameraId] = useState(0);
  const [zones, setZones] = useState<Zone[]>([]);
  const [draftPoints, setDraftPoints] = useState<Point[]>([]);
  const [riskLevel, setRiskLevel] = useState('CAUTION');
  const [status, setStatus] = useState<string>('');

  useEffect(() => {
    axios
      .get(`${API_URL}/api/zones/${cameraId}`)
      .then((res) => setZones(res.data))
      .catch(() => setZones([]));
    setDraftPoints([]);
  }, [cameraId]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (!canvas || !ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#0f172a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const drawPolygon = (points: Point[], stroke: string, fill: string, close: boolean) => {
      if (points.length === 0) return;
      ctx.beginPath();
      ctx.moveTo(points[0].x, points[0].y);
      points.slice(1).forEach((p) => ctx.lineTo(p.x, p.y));
      if (close) ctx.closePath();
      ctx.strokeStyle = stroke;
      ctx.lineWidth = 2;
      ctx.stroke();
      if (close) {
        ctx.fillStyle = fill;
        ctx.fill();
      }
      points.forEach((p) => {
        ctx.beginPath();
        ctx.arc(p.x, p.y, 3, 0, 2 * Math.PI);
        ctx.fillStyle = stroke;
        ctx.fill();
      });
    };

    zones.forEach((z) => {
      const color = z.risk_level === 'CRITICAL' ? '#ef4444' : '#f59e0b';
      drawPolygon(z.polygon, color, color + '33', true);
    });

    drawPolygon(draftPoints, '#22d3ee', '#22d3ee22', false);
  }, [zones, draftPoints]);

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = Math.round(((e.clientX - rect.left) / rect.width) * canvas.width);
    const y = Math.round(((e.clientY - rect.top) / rect.height) * canvas.height);
    setDraftPoints((prev) => [...prev, { x, y }]);
  };

  const saveZone = async () => {
    if (draftPoints.length < 3) {
      setStatus('Need at least 3 points to form a zone.');
      return;
    }
    const name = `zone_${zones.length + 1}`;
    const updated = [...zones, { name, polygon: draftPoints, risk_level: riskLevel }];
    try {
      const res = await axios.post(`${API_URL}/api/zones/${cameraId}`, updated);
      setZones(res.data);
      setDraftPoints([]);
      setStatus(`Saved "${name}" (${riskLevel}).`);
    } catch (err) {
      setStatus('Failed to save zone — is the backend running?');
    }
  };

  const clearZones = async () => {
    try {
      const res = await axios.post(`${API_URL}/api/zones/${cameraId}`, []);
      setZones(res.data);
      setDraftPoints([]);
      setStatus('Cleared all zones for this camera.');
    } catch {
      setStatus('Failed to clear zones — is the backend running?');
    }
  };

  return (
    <div className="bg-slate-800 p-4 rounded-xl border border-slate-700 shadow-lg h-full">
      <h2 className="text-xl font-bold mb-4">Zone Editor</h2>

      <div className="flex items-center gap-3 mb-3 text-sm">
        <label className="text-slate-400">Camera</label>
        <input
          type="number"
          value={cameraId}
          onChange={(e) => setCameraId(Number(e.target.value))}
          className="w-16 bg-slate-900 border border-slate-700 rounded px-2 py-1"
        />
        <label className="text-slate-400">Risk level</label>
        <select
          value={riskLevel}
          onChange={(e) => setRiskLevel(e.target.value)}
          className="bg-slate-900 border border-slate-700 rounded px-2 py-1"
        >
          <option value="CAUTION">CAUTION</option>
          <option value="CRITICAL">CRITICAL</option>
        </select>
      </div>

      <canvas
        ref={canvasRef}
        width={640}
        height={480}
        onClick={handleCanvasClick}
        className="w-full h-48 bg-slate-900 rounded-lg border border-slate-800 cursor-crosshair"
      />

      <div className="flex items-center gap-2 mt-3 text-sm">
        <button
          onClick={saveZone}
          className="px-3 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white"
        >
          Save Zone ({draftPoints.length} pts)
        </button>
        <button
          onClick={() => setDraftPoints([])}
          className="px-3 py-1 rounded bg-slate-700 hover:bg-slate-600 text-white"
        >
          Reset Draft
        </button>
        <button
          onClick={clearZones}
          className="px-3 py-1 rounded bg-red-900 hover:bg-red-800 text-white"
        >
          Clear All
        </button>
      </div>
      {status && <div className="text-xs text-slate-400 mt-2">{status}</div>}
    </div>
  );
}
