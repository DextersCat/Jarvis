import { useState } from 'react';
import NeuralNetwork, { type CoreState } from '../NeuralNetwork';
import { Button } from '@/components/ui/button';

export default function NeuralNetworkExample() {
  const [state, setState] = useState<CoreState>('online');

  const states: CoreState[] = ['offline', 'online', 'listening', 'processing', 'speaking', 'stopped'];

  return (
    <div className="h-screen w-full bg-background p-8 flex flex-col gap-4">
      <div className="flex gap-2 flex-wrap">
        {states.map(s => (
          <Button
            key={s}
            size="sm"
            variant={state === s ? 'default' : 'outline'}
            onClick={() => setState(s)}
            data-testid={`button-${s}`}
          >
            {s}
          </Button>
        ))}
      </div>
      <div className="flex-1 border border-primary/30 rounded-md">
        <NeuralNetwork state={state} />
      </div>
    </div>
  );
}
