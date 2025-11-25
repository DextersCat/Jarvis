import { Button } from '@/components/ui/button';

interface ControlButtonsProps {
  onStartJarvis: () => void;
  onStopJarvis: () => void;
  onTestTime: () => void;
  onCheckBrain: () => void;
  isRunning: boolean;
  className?: string;
}

export default function ControlButtons({
  onStartJarvis,
  onStopJarvis,
  onTestTime,
  onCheckBrain,
  isRunning,
  className = '',
}: ControlButtonsProps) {
  return (
    <div className={`flex flex-wrap gap-3 ${className}`}>
      <Button
        variant="outline"
        onClick={onStartJarvis}
        disabled={isRunning}
        className="border-primary/50 hover:border-primary text-primary uppercase tracking-wider text-xs font-semibold px-6"
        data-testid="button-start-jarvis"
      >
        Start Jarvis
      </Button>
      <Button
        variant="outline"
        onClick={onStopJarvis}
        disabled={!isRunning}
        className="border-destructive/50 hover:border-destructive text-destructive uppercase tracking-wider text-xs font-semibold px-6"
        data-testid="button-stop-jarvis"
      >
        Stop Jarvis
      </Button>
      <Button
        variant="outline"
        onClick={onTestTime}
        className="border-primary/30 hover:border-primary/60 uppercase tracking-wider text-xs font-semibold px-6"
        data-testid="button-test-time"
      >
        Test Time
      </Button>
      <Button
        variant="outline"
        onClick={onCheckBrain}
        className="border-primary/30 hover:border-primary/60 uppercase tracking-wider text-xs font-semibold px-6"
        data-testid="button-check-brain"
      >
        Check Brain
      </Button>
    </div>
  );
}
