import { Card } from '@/components/ui/card';

interface StatusItem {
  label: string;
  value: string | number;
  highlight?: boolean;
}

interface StatusPanelProps {
  title: string;
  items: StatusItem[];
  className?: string;
}

export default function StatusPanel({ title, items, className = '' }: StatusPanelProps) {
  return (
    <Card className={`p-6 border-primary/30 bg-card/70 backdrop-blur-sm ${className}`} data-testid={`panel-${title.toLowerCase().replace(/\s+/g, '-')}`}>
      <h2 className="text-sm font-semibold uppercase tracking-widest text-primary mb-6" data-testid="text-panel-title">
        {title}
      </h2>
      <div className="space-y-4">
        {items.map((item, index) => (
          <div key={index}>
            <div className="text-xs uppercase tracking-wide text-muted-foreground mb-1" data-testid={`label-${item.label.toLowerCase().replace(/\s+/g, '-')}`}>
              {item.label}
            </div>
            <div 
              className={`text-sm font-medium ${item.highlight ? 'text-primary' : 'text-foreground'}`}
              data-testid={`value-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
            >
              {item.value}
            </div>
            {index < items.length - 1 && (
              <div className="h-px bg-border/20 mt-4" />
            )}
          </div>
        ))}
      </div>
    </Card>
  );
}
