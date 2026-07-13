import React, { useRef, useEffect } from 'react';

interface BBox {
  bbox: number[];
  risk_score: number;
}

interface FrameData {
  camera_id: string;
  frame: string;
  detections: BBox[];
  poses: any[];
}

export default function LiveFeedGrid({ liveFrame }: { liveFrame: FrameData | null }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!liveFrame || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    img.onload = () => {
      // Clear and draw image
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      
      // Draw detections
      liveFrame.detections.forEach(det => {
        const [x1, y1, x2, y2] = det.bbox;
        
        ctx.strokeStyle = det.risk_score > 0.8 ? 'red' : (det.risk_score > 0.5 ? 'orange' : 'green');
        ctx.lineWidth = 3;
        ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
        
        ctx.fillStyle = ctx.strokeStyle;
        ctx.font = '16px Arial';
        ctx.fillText(`Risk: ${det.risk_score.toFixed(2)}`, x1, y1 - 5);
      });
      
      // Draw poses (simplified)
      liveFrame.poses.forEach(pose => {
        pose.forEach((kp: number[]) => {
          ctx.fillStyle = 'blue';
          ctx.beginPath();
          ctx.arc(kp[0], kp[1], 4, 0, 2 * Math.PI);
          ctx.fill();
        });
      });
    };
    img.src = `data:image/jpeg;base64,${liveFrame.frame}`;
  }, [liveFrame]);

  return (
    <div className="bg-slate-800 p-4 rounded-xl border border-slate-700 shadow-lg">
      <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
        <span className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></span>
        Live Feed {liveFrame ? `- Camera ${liveFrame.camera_id}` : ''}
      </h2>
      <div className="relative aspect-video bg-black rounded-lg overflow-hidden flex items-center justify-center">
        <canvas 
          ref={canvasRef} 
          width={640} 
          height={480}
          className="max-w-full max-h-full object-contain"
        />
        {!liveFrame && (
          <div className="absolute inset-0 flex items-center justify-center text-slate-500">
            Waiting for video stream...
          </div>
        )}
      </div>
    </div>
  );
}
