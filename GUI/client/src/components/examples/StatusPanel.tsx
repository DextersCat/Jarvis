import StatusPanel from '../StatusPanel';

export default function StatusPanelExample() {
  const aiPiItems = [
    { label: 'Loop', value: 'RUNNING', highlight: true },
    { label: 'Wake', value: 'PTT', highlight: false },
    { label: 'Local Time', value: new Date().toLocaleTimeString(), highlight: false },
    { label: 'Last Audio', value: '14:23:45', highlight: false },
  ];

  const brainItems = [
    { label: 'Brain', value: 'ONLINE', highlight: true },
    { label: 'Model', value: 'Local LLM', highlight: false },
    { label: 'Last Action', value: 'TIME_INTENT handled', highlight: false },
  ];

  return (
    <div className="h-screen w-full bg-background p-8 flex gap-6">
      <StatusPanel title="AI-Pi" items={aiPiItems} className="w-80" />
      <StatusPanel title="Brain" items={brainItems} className="w-80" />
    </div>
  );
}
