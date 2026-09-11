import React from 'react';

export interface GlazeCardProps extends React.HTMLAttributes<HTMLDivElement> {
  elevated?: boolean;
}

export function GlazeCard({ elevated = false, className = '', children, ...props }: GlazeCardProps) {
  return (
    <div
      className={`glaze-card ${elevated ? 'glaze-card-elevated' : ''} ${className}`.trim()}
      {...props}
    >
      {children}
    </div>
  );
}
