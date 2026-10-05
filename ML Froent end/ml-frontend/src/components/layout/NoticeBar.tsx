import { useState, useEffect } from 'react';

export default function NoticeBar() {
  const [pulse, setPulse] = useState(true);

  useEffect(() => {
    const interval = setInterval(() => {
      setPulse((prev) => !prev);
    }, 1500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div
      className="h-8 w-full px-6 flex items-center justify-between"
      style={{
        backgroundColor: '#1E293B',
        color: '#E2E8F0',
        fontSize: '12px',
      }}
    >
      <div className="flex items-center gap-2">
        <span
          className="w-1.5 h-1.5 rounded-full"
          style={{ backgroundColor: '#0E7C7E' }}
        />
        <span>
          Research prototype · Synthetic data · Not for real lending decisions
        </span>
      </div>
      <div className="flex items-center gap-2">
        <span className="relative flex h-2 w-2">
          <span
            className="absolute inline-flex h-full w-full rounded-full opacity-75"
            style={{
              backgroundColor: '#3FB950',
              animation: pulse ? 'ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite' : 'none',
            }}
          />
          <span
            className="relative inline-flex rounded-full h-2 w-2"
            style={{ backgroundColor: '#3FB950' }}
          />
        </span>
        <span>Online</span>
      </div>
    </div>
  );
}
