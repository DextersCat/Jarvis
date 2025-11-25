import { useEffect, useRef } from 'react';

interface Node {
  x: number;
  y: number;
  vx: number;
  vy: number;
}

interface Connection {
  from: number;
  to: number;
}

export type CoreState = 'offline' | 'online' | 'listening' | 'processing' | 'speaking' | 'stopped';

interface NeuralNetworkProps {
  state: CoreState;
  className?: string;
}

export default function NeuralNetwork({ state, className = '' }: NeuralNetworkProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const nodesRef = useRef<Node[]>([]);
  const connectionsRef = useRef<Connection[]>([]);
  const animationRef = useRef<number>();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resizeCanvas = () => {
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * window.devicePixelRatio;
      canvas.height = rect.height * window.devicePixelRatio;
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    };

    resizeCanvas();

    const nodeCount = 20;
    const centerX = canvas.offsetWidth / 2;
    const centerY = canvas.offsetHeight / 2;
    const radius = Math.min(canvas.offsetWidth, canvas.offsetHeight) * 0.35;

    if (nodesRef.current.length === 0) {
      for (let i = 0; i < nodeCount; i++) {
        const angle = (i / nodeCount) * Math.PI * 2;
        const distance = radius * (0.5 + Math.random() * 0.5);
        nodesRef.current.push({
          x: centerX + Math.cos(angle) * distance,
          y: centerY + Math.sin(angle) * distance,
          vx: (Math.random() - 0.5) * 0.3,
          vy: (Math.random() - 0.5) * 0.3,
        });
      }

      for (let i = 0; i < nodeCount; i++) {
        const connections = Math.floor(Math.random() * 3) + 1;
        for (let j = 0; j < connections; j++) {
          const to = Math.floor(Math.random() * nodeCount);
          if (to !== i) {
            connectionsRef.current.push({ from: i, to });
          }
        }
      }
    }

    let pulseTime = 0;
    let thinkingPulse = 0;

    const animate = () => {
      ctx.clearRect(0, 0, canvas.offsetWidth, canvas.offsetHeight);

      const isOffline = state === 'offline' || state === 'stopped';
      const isThinking = state === 'processing';
      const isActive = state === 'listening' || state === 'speaking' || state === 'online';

      pulseTime += isOffline ? 0.005 : 0.015;
      if (isThinking) {
        thinkingPulse += 0.1;
      }

      const baseOpacity = isOffline ? 0.2 : isActive ? 0.6 : 0.5;
      const pulseIntensity = Math.sin(pulseTime) * 0.2 + 0.8;
      const thinkingIntensity = isThinking ? Math.sin(thinkingPulse) * 0.3 + 0.7 : 1;

      nodesRef.current.forEach((node, i) => {
        if (!isOffline) {
          node.x += node.vx;
          node.y += node.vy;

          const dx = centerX - node.x;
          const dy = centerY - node.y;
          const distance = Math.sqrt(dx * dx + dy * dy);
          
          if (distance > radius) {
            node.vx *= -1;
            node.vy *= -1;
          }

          if (distance < radius * 0.2) {
            node.vx = (Math.random() - 0.5) * 0.5;
            node.vy = (Math.random() - 0.5) * 0.5;
          }
        }
      });

      connectionsRef.current.forEach(conn => {
        const from = nodesRef.current[conn.from];
        const to = nodesRef.current[conn.to];

        const gradient = ctx.createLinearGradient(from.x, from.y, to.x, to.y);
        const lineOpacity = baseOpacity * pulseIntensity * thinkingIntensity * 0.4;
        
        gradient.addColorStop(0, `rgba(0, 217, 255, ${lineOpacity})`);
        gradient.addColorStop(0.5, `rgba(0, 217, 255, ${lineOpacity * 1.5})`);
        gradient.addColorStop(1, `rgba(0, 217, 255, ${lineOpacity})`);

        ctx.beginPath();
        ctx.moveTo(from.x, from.y);
        ctx.lineTo(to.x, to.y);
        ctx.strokeStyle = gradient;
        ctx.lineWidth = isThinking ? 2 : 1;
        ctx.stroke();
      });

      nodesRef.current.forEach(node => {
        const nodeOpacity = baseOpacity * pulseIntensity * thinkingIntensity;
        const glowSize = isThinking ? 15 : isOffline ? 5 : 10;

        ctx.shadowBlur = glowSize;
        ctx.shadowColor = `rgba(0, 217, 255, ${nodeOpacity * 0.8})`;
        
        ctx.beginPath();
        ctx.arc(node.x, node.y, isThinking ? 5 : 4, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0, 217, 255, ${nodeOpacity})`;
        ctx.fill();

        ctx.shadowBlur = 0;
      });

      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [state]);

  const getStatusText = () => {
    switch (state) {
      case 'offline': return 'OFFLINE';
      case 'stopped': return 'STOPPED';
      case 'listening': return 'LISTENING';
      case 'processing': return 'PROCESSING';
      case 'speaking': return 'SPEAKING';
      case 'online': return 'ONLINE';
      default: return 'UNKNOWN';
    }
  };

  const getStatusColor = () => {
    switch (state) {
      case 'offline':
      case 'stopped':
        return 'text-muted-foreground';
      case 'processing':
        return 'text-primary text-glow';
      default:
        return 'text-primary';
    }
  };

  return (
    <div className={`flex flex-col items-center justify-center h-full ${className}`}>
      <canvas
        ref={canvasRef}
        className="w-full h-full"
        style={{ maxHeight: '400px' }}
        data-testid="canvas-neural-network"
      />
      <div className={`mt-4 text-sm font-semibold uppercase tracking-widest ${getStatusColor()} transition-colors duration-300`} data-testid="text-status">
        Status: {getStatusText()}
      </div>
    </div>
  );
}
