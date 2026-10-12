import type { ReactNode } from 'react';
import styles from './DataTable.module.css';

export interface Column {
  key: string;
  label: string;
  width?: string;
}

interface DataTableProps {
  caption: string;
  columns: Column[];
  rows: Array<{ id: string; cells: ReactNode[] }>;
  minWidth?: number;
}

export function DataTable({ caption, columns, rows, minWidth }: DataTableProps) {
  return (
    <div className={styles.wrap}>
      <table className={styles.table} style={minWidth ? { minWidth } : undefined}>
        <caption className="visually-hidden">{caption}</caption>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key} scope="col" style={column.width ? { width: column.width } : undefined}>
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              {row.cells.map((cell, index) => {
                if (index === 0) {
                  return (
                    <th key={columns[index].key} scope="row" style={{ textAlign: 'left' }}>
                      {cell}
                    </th>
                  );
                }
                return <td key={columns[index].key}>{cell}</td>;
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
