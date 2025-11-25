import { useState } from 'react';
import ControlButtons from '../ControlButtons';

export default function ControlButtonsExample() {
  const [isRunning, setIsRunning] = useState(false);

  return (
    <div className="h-screen w-full bg-background p-8 flex items-center justify-center">
      <ControlButtons
        onStartJarvis={() => {
          console.log('Start Jarvis clicked');
          setIsRunning(true);
        }}
        onStopJarvis={() => {
          console.log('Stop Jarvis clicked');
          setIsRunning(false);
        }}
        onTestTime={() => console.log('Test Time clicked')}
        onCheckBrain={() => console.log('Check Brain clicked')}
        isRunning={isRunning}
      />
    </div>
  );
}
