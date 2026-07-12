import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hoverLift?: boolean;
  glass?: boolean;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className = '', hoverLift = false, glass = false, children, ...props }, ref) => {
    const baseStyle = `rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm dark:border-zinc-800/80 dark:bg-zinc-900/60 transition-all duration-300 ease-out ${
      glass ? 'backdrop-blur-md bg-white/70 dark:bg-zinc-950/50' : ''
    } ${
      hoverLift ? 'hover:-translate-y-1 hover:shadow-md hover:shadow-emerald-950/5 cursor-pointer hover:border-emerald-500/20 dark:hover:border-emerald-500/10' : ''
    }`;

    return (
      <div ref={ref} className={`${baseStyle} ${className}`} {...props}>
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';

export const CardHeader = ({ className = '', children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={`flex flex-col space-y-1.5 pb-4 ${className}`} {...props}>
    {children}
  </div>
);

export const CardTitle = ({ className = '', children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) => (
  <h3 className={`text-lg font-bold tracking-tight text-slate-800 dark:text-zinc-100 ${className}`} {...props}>
    {children}
  </h3>
);

export const CardDescription = ({ className = '', children, ...props }: React.HTMLAttributes<HTMLParagraphElement>) => (
  <p className={`text-xs text-slate-500 dark:text-zinc-400 ${className}`} {...props}>
    {children}
  </p>
);

export const CardContent = ({ className = '', children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={`${className}`} {...props}>
    {children}
  </div>
);

export const CardFooter = ({ className = '', children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={`flex items-center pt-4 ${className}`} {...props}>
    {children}
  </div>
);
