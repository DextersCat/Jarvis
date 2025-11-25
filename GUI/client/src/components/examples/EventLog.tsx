import { useState } from 'react';
import EventLog, { type LogEvent } from '../EventLog';
import { Button } from '@/components/ui/button';

export default function EventLogExample() {
  const [events, setEvents] = useState<LogEvent[]>([
    { timestamp: '14:20:15', message: 'System initialized' },
    { timestamp: '14:20:16', message: 'AI-Pi loop started' },
    { timestamp: '14:20:18', message: 'Brain connection established' },
    { timestamp: '14:21:32', message: 'Wake word detected' },
    { timestamp: '14:21:33', message: 'Audio captured: 2.3s' },
    { timestamp: '14:21:35', message: 'Processing speech input' },
    { timestamp: '14:21:37', message: 'Intent recognized: TIME_QUERY' },
    { timestamp: '14:21:38', message: 'Response generated' },
  ]);

  const addEvent = () => {
    const now = new Date();
    const timestamp = now.toTimeString().split(' ')[0];
    const messages = [
      'User interaction detected',
      'Processing request',
      'Brain query complete',
      'Audio playback started',
      'System status: nominal',
    ];
    const message = messages[Math.floor(Math.random() * messages.length)];
    
    setEvents(prev => [...prev, { timestamp, message }]);
  };

  return (
    <div className="h-screen w-full bg-background p-8 flex flex-col gap-4">
      <Button onClick={addEvent} size="sm" data-testid="button-add-event">
        Add Event
      </Button>
      <EventLog events={events} className="w-full max-w-3xl" />
    </div>
  );
}
