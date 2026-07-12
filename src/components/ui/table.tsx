import React from 'react';

export const Table = ({ className = '', children, ...props }: React.HTMLAttributes<HTMLTableElement>) => (
  <div className="w-full overflow-x-auto rounded-xl border border-slate-200/60 dark:border-zinc-800/60">
    <table className={`w-full min-w-[640px] border-collapse text-left text-sm ${className}`} {...props}>
      {children}
    </table>
  </div>
);

export const TableHeader = ({ className = '', children, ...props }: React.HTMLAttributes<HTMLTableSectionElement>) => (
  <thead className={`bg-slate-50/70 border-b border-slate-200/80 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:bg-zinc-900/50 dark:border-zinc-800/80 dark:text-zinc-400 ${className}`} {...props}>
    {children}
  </thead>
);

export const TableBody = ({ className = '', children, ...props }: React.HTMLAttributes<HTMLTableSectionElement>) => (
  <tbody className={`divide-y divide-slate-200/50 dark:divide-zinc-800/50 ${className}`} {...props}>
    {children}
  </tbody>
);

export const TableRow = ({ className = '', children, ...props }: React.HTMLAttributes<HTMLTableRowElement>) => (
  <tr className={`hover:bg-slate-50/50 transition-colors dark:hover:bg-zinc-900/20 ${className}`} {...props}>
    {children}
  </tr>
);

export const TableHead = ({ className = '', children, ...props }: React.HTMLAttributes<HTMLTableCellElement>) => (
  <th className={`px-6 py-4 font-semibold text-slate-600 dark:text-zinc-300 ${className}`} {...props}>
    {children}
  </th>
);

export const TableCell = ({ className = '', children, ...props }: React.HTMLAttributes<HTMLTableCellElement>) => (
  <td className={`px-6 py-4 text-slate-600 dark:text-zinc-300 align-middle ${className}`} {...props}>
    {children}
  </td>
);
