import type { ReactNode } from 'react';

/** 右侧工具参数区统一容器：占满可用高度并可滚动 */
export function ToolPanel({ children }: { children: ReactNode }) {
  return (
    <div className="flex flex-col gap-4 p-4 w-full min-w-0">{children}</div>
  );
}
