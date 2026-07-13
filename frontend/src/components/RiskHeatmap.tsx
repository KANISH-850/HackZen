import { useEffect, useState } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface RiskLog {
  id: number;
  worker_id: number;
  timestamp: string;
  risk_score: number;
}

// Sequential ramp: low risk -> high risk, one hue (red), light -> dark/saturated.
function cellColor(score: number | undefined): string {
  if (score === undefined) return '#1e293b'; // slate-800, "no data"
  if (score < 0.2) return '#450a0a1a'; // near-transparent
  if (score < 0.4) return '#7f1d1d';
  if (score < 0.6) return '#b91c1c';
  if (score < 0.8) return '#dc2626';
  return '#ef4444';
}

const BUCKETS = 12;

export default function RiskHeatmap() {
  const [logs, setLogs] = useState<RiskLog[]>([]);
  const [showTable, setShowTable] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchLogs = () => {
      axios
        .get(`${API_URL}/api/risk_logs`, { params: { limit: 300 } })
        .then((res) => {
          setLogs(res.data);
          setError(null);
        })
        .catch(() => setError('Unable to reach backend'));
    };
    fetchLogs();
    const interval = setInterval(fetchLogs, 5000);
    return () => clearInterval(interval);
  }, []);

  const workerIds = Array.from(new Set(logs.map((l) => l.worker_id))).sort((a, b) => a - b);

  // For each worker, take their most recent BUCKETS readings (most recent first, then reversed
  // so the grid reads oldest -> newest left to right).
  const grid = workerIds.map((wid) => {
    const workerLogs = logs.filter((l) => l.worker_id === wid).slice(0, BUCKETS).reverse();
    const cells = Array.from({ length: BUCKETS }, (_, i) => workerLogs[i]);
    return { workerId: wid, cells };
  });

  return (
    <div className="bg-slate-800 p-4 rounded-xl border border-slate-700 shadow-lg h-full">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-xl font-bold">Risk Heatmap</h2>
        <button
          onClick={() => setShowTable((v) => !v)}
          className="text-xs text-slate-400 hover:text-slate-200 underline"
        >
          {showTable ? 'Show grid' : 'Show table'}
        </button>
      </div>

      {error && <div className="text-sm text-red-400">{error}</div>}

      {!error && workerIds.length === 0 && (
        <div className="h-40 flex items-center justify-center text-slate-500 text-sm border border-slate-800 rounded-lg bg-slate-900">
          No risk data yet — waiting for tracked workers
        </div>
      )}

      {!error && workerIds.length > 0 && !showTable && (
        <div className="overflow-x-auto">
          <table className="text-xs">
            <tbody>
              {grid.map(({ workerId, cells }) => (
                <tr key={workerId}>
                  <td className="pr-2 text-slate-400 whitespace-nowrap">Worker {workerId}</td>
                  {cells.map((c, i) => (
                    <td key={i} className="p-0.5">
                      <div
                        title={c ? `Worker ${workerId} — risk ${c.risk_score.toFixed(2)} at ${new Date(c.timestamp).toLocaleTimeString()}` : 'No data'}
                        className="w-5 h-5 rounded-sm border border-slate-900"
                        style={{ backgroundColor: cellColor(c?.risk_score) }}
                      />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          <div className="flex items-center gap-2 mt-3 text-[10px] text-slate-400">
            <span>oldest</span>
            <div className="flex-1 h-3 rounded" style={{ background: 'linear-gradient(to right, #450a0a1a, #ef4444)' }} />
            <span>newest / higher risk</span>
          </div>
        </div>
      )}

      {!error && workerIds.length > 0 && showTable && (
        <div className="max-h-48 overflow-y-auto text-xs">
          <table className="w-full text-left">
            <thead className="text-slate-400">
              <tr>
                <th className="pr-2">Worker</th>
                <th className="pr-2">Risk score</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {logs.slice(0, 50).map((l) => (
                <tr key={l.id} className="border-t border-slate-700/50">
                  <td className="pr-2 text-slate-300">{l.worker_id}</td>
                  <td className="pr-2 text-slate-300">{l.risk_score.toFixed(2)}</td>
                  <td className="text-slate-500">{new Date(l.timestamp).toLocaleTimeString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
