import { useEffect, useRef } from 'react';
import { Card } from '@/components/ui/card';

export interface LogEvent {
  timestamp: string;
  message: string;
}

interface EventLogProps {
  events: LogEvent[];
  className?: string;
}

export default function EventLog({ events, className = '' }: EventLogProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events]);

  return (
    <Card className={`p-4 border-primary/30 bg-card/70 backdrop-blur-sm ${className}`} data-testid="panel-event-log">
      <h3 className="text-xs font-semibold uppercase tracking-widest text-primary mb-3" data-testid="text-event-log-title">
        Event Log
      </h3>
      <div 
        ref={scrollRef}
        className="space-y-1 overflow-y-auto scrollbar-thin max-h-32"
        data-testid="container-events"
      >
        {events.length === 0 ? (
          <div className="text-xs text-muted-foreground font-mono" data-testid="text-no-events">
            No events yet...
          </div>
        ) : (
          events.map((event, index) => (
            <div
              key={index}
              className={`text-xs font-mono py-1 px-2 rounded ${
                index % 2 === 0 ? 'bg-background/30' : 'bg-background/10'
              }`}
              data-testid={`event-${index}`}
            >
              <span className="text-primary" data-testid={`event-timestamp-${index}`}>[{event.timestamp}]</span>{' '}
              <span className="text-foreground" data-testid={`event-message-${index}`}>{event.message}</span>
            </div>
          ))
        )}
      </div>
    </Card>
  );
}
