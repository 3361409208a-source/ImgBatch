import { useCallback, type MouseEvent as ReactMouseEvent } from 'react';

interface ResizeHandleProps {
  /** 拖拽开始时读取的基准宽度 */
  getSize: () => number;
  /** 'left'：向右拖增大左侧栏；'right'：向右拖减小右侧栏 */
  direction: 'left' | 'right';
  min: number;
  max: number;
  /** 拖拽过程中实时回调新宽度 */
  onResize: (size: number) => void;
  /** 拖拽结束时回调最终宽度（用于持久化） */
  onResizeEnd?: (size: number) => void;
  /** 双击时重置到的默认宽度 */
  defaultSize?: number;
  ariaLabel?: string;
}

const clamp = (n: number, min: number, max: number) => Math.min(max, Math.max(min, n));

export function ResizeHandle({
  getSize,
  direction,
  min,
  max,
  onResize,
  onResizeEnd,
  defaultSize,
  ariaLabel,
}: ResizeHandleProps) {
  const handleMouseDown = useCallback(
    (e: ReactMouseEvent) => {
      e.preventDefault();
      const startX = e.clientX;
      const startSize = getSize();
      let latest = startSize;

      const onMove = (ev: MouseEvent) => {
        const dx = ev.clientX - startX;
        const raw = direction === 'left' ? startSize + dx : startSize - dx;
        latest = clamp(raw, min, max);
        onResize(latest);
      };
      const onUp = () => {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        onResizeEnd?.(latest);
      };

      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
    },
    [getSize, direction, min, max, onResize, onResizeEnd],
  );

  const handleDoubleClick = useCallback(() => {
    if (defaultSize == null) return;
    const size = clamp(defaultSize, min, max);
    onResize(size);
    onResizeEnd?.(size);
  }, [defaultSize, min, max, onResize, onResizeEnd]);

  return (
    <div
      role="separator"
      aria-orientation="vertical"
      aria-label={ariaLabel}
      onMouseDown={handleMouseDown}
      onDoubleClick={handleDoubleClick}
      className="group relative w-1 shrink-0 cursor-col-resize select-none"
    >
      <div className="pointer-events-none absolute inset-y-0 left-1/2 w-px -translate-x-1/2 bg-border transition-colors group-hover:bg-primary group-active:bg-primary" />
    </div>
  );
}
