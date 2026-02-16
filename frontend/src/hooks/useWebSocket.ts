import { useEffect, useRef, useCallback } from "react";
import { useStore } from "../store/useStore";

interface WebSocketMessage {
  type:
    | "monitor_event"
    | "task_update"
    | "status_update"
    | "heartbeat"
    | "pong";
  data?: any;
}

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(
    null,
  );
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 10;

  const {
    setConnected,
    addEvent,
    updateTask,
    setStats,
    setMonitorsRunning,
    setShopifyStores,
  } = useStore();

  const handleMessage = useCallback(
    (message: WebSocketMessage) => {
      switch (message.type) {
        case "monitor_event":
          if (message.data) {
            addEvent(message.data);
            // Update stats
            setStats({
              totalProductsFound:
                useStore.getState().stats.totalProductsFound + 1,
              highPriorityFound:
                message.data.priority === "high"
                  ? useStore.getState().stats.highPriorityFound + 1
                  : useStore.getState().stats.highPriorityFound,
            });
          }
          break;

        case "task_update":
          if (message.data) {
            updateTask(message.data.id, message.data);
          }
          break;

        case "status_update":
          if (message.data) {
            if (message.data.monitorsRunning !== undefined) {
              setMonitorsRunning(message.data.monitorsRunning);
            }
            if (message.data.stats) {
              setStats(message.data.stats);
            }
            if (message.data.shopifyStores) {
              setShopifyStores(message.data.shopifyStores);
            }
          }
          break;

        case "heartbeat":
          // Just keep-alive, no action needed
          break;
      }
    },
    [addEvent, setStats, updateTask, setMonitorsRunning, setShopifyStores],
  );

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    // Use configured API URL or fallback to window location
    const apiUrl = import.meta.env.VITE_API_URL;
    let wsUrl: string;

    if (apiUrl) {
      try {
        const url = new URL(apiUrl);
        const protocol = url.protocol === "https:" ? "wss:" : "ws:";
        wsUrl = `${protocol}//${url.host}/ws/events`;
      } catch (e) {
        // Fallback if URL is invalid
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        wsUrl = `${protocol}//${window.location.host}/ws/events`;
      }
    } else {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      wsUrl = `${protocol}//${window.location.host}/ws/events`;
    }

    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log("[WebSocket] Connected");
        setConnected(true);
        reconnectAttempts.current = 0;
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as WebSocketMessage;
          handleMessage(message);
        } catch (e) {
          console.error("[WebSocket] Parse error:", e);
        }
      };

      wsRef.current.onclose = () => {
        console.log("[WebSocket] Disconnected");
        setConnected(false);

        // Reconnect with exponential backoff
        if (reconnectAttempts.current < maxReconnectAttempts) {
          const delay = Math.min(
            1000 * Math.pow(2, reconnectAttempts.current),
            30000,
          );
          reconnectAttempts.current++;
          console.log(
            `[WebSocket] Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current})`,
          );

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error("[WebSocket] Error:", error);
      };
    } catch (e) {
      console.error("[WebSocket] Connection error:", e);
    }
  }, [setConnected, handleMessage]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setConnected(false);
  }, [setConnected]);

  const sendPing = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send("ping");
    }
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    connect();

    // Ping every 25 seconds to keep connection alive
    const pingInterval = setInterval(sendPing, 25000);

    return () => {
      clearInterval(pingInterval);
      disconnect();
    };
  }, [connect, disconnect, sendPing]);

  return {
    isConnected: useStore((state) => state.isConnected),
    connect,
    disconnect,
    sendPing,
  };
}
