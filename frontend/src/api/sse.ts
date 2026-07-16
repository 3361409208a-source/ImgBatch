import { getApiBase, resetApiBaseCache } from './client';

export function subscribeTask(
  taskId: string,
  onProgress: (pct: number, message: string) => void,
  onDone: (status: string, result: unknown) => void,
): () => void {
  let closed = false;
  let es: EventSource | null = null;

  (async () => {
    let base: string;
    try {
      base = await getApiBase();
    } catch {
      if (!closed) onDone('error', { error: 'API not ready' });
      return;
    }
    if (closed) return;

    const connect = (urlBase: string) => {
      es?.close();
      es = new EventSource(`${urlBase}/tasks/${taskId}/events`);

      es.addEventListener('progress', (e: MessageEvent) => {
        const d = JSON.parse(e.data);
        onProgress(d.pct, d.message);
      });

      es.addEventListener('done', (e: MessageEvent) => {
        const d = JSON.parse(e.data);
        onDone(d.status, d.result);
        es?.close();
      });

      let retried = false;
      es.onerror = () => {
        if (closed) {
          es?.close();
          return;
        }
        if (!retried) {
          retried = true;
          es?.close();
          resetApiBaseCache();
          void getApiBase(true)
            .then((b) => {
              if (!closed) connect(b);
            })
            .catch(() => {
              onDone('error', { error: 'SSE connection lost' });
            });
          return;
        }
        es?.close();
      };
    };

    connect(base);
  })();

  return () => {
    closed = true;
    es?.close();
  };
}
