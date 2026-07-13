export default function AlertPanel({ alerts }: { alerts: any[] }) {
  return (
    <div className="bg-slate-800 p-4 rounded-xl border border-slate-700 shadow-lg h-full max-h-[500px] flex flex-col">
      <h2 className="text-xl font-bold mb-4">Live Alerts</h2>
      <div className="flex-1 overflow-y-auto space-y-3 pr-2">
        {alerts.length === 0 ? (
          <div className="text-slate-400 text-center py-8">No recent alerts</div>
        ) : (
          alerts.map((alert, i) => (
            <div 
              key={i} 
              className={`p-3 rounded-lg border flex items-start gap-3 ${
                alert.severity === 'CRITICAL' 
                  ? 'bg-red-900/20 border-red-500/50 text-red-200' 
                  : 'bg-orange-900/20 border-orange-500/50 text-orange-200'
              }`}
            >
              {alert.severity === 'CRITICAL' ? (
                <span className="text-red-500 font-bold text-xl shrink-0">!</span>
              ) : (
                <span className="text-orange-500 font-bold text-xl shrink-0">i</span>
              )}
              <div>
                <div className="font-bold">{alert.severity} RISK</div>
                <div className="text-sm opacity-80">Camera {alert.camera_id} - Worker {alert.worker_id}</div>
                <div className="text-xs mt-1 opacity-70">
                  {JSON.stringify(alert.details)}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
