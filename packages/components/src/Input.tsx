import React from 'react';

export interface GlazeInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

export function GlazeInput({ label, className = '', ...props }: GlazeInputProps) {
  return (
    <label className="glaze-input-wrapper">
      {label && <span className="glaze-input-label">{label}</span>}
      <input className={`glaze-input ${className}`.trim()} {...props} />
    </label>
  );
}
