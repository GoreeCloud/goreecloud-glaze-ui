import type { ButtonHTMLAttributes, ReactNode } from 'react';
import './button.css';

export type GlazeButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';

export interface GlazeButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: GlazeButtonVariant;
  children: ReactNode;
}

export function GlazeButton({
  variant = 'primary',
  children,
  className = '',
  ...props
}: GlazeButtonProps) {
  return (
    <button
      className={`glaze-button glaze-button-${variant} ${className}`.trim()}
      {...props}
    >
      {children}
    </button>
  );
}
