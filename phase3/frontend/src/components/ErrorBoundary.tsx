import { Component, type ErrorInfo, type ReactNode } from "react";
import { logger } from "@/lib/logger";

interface Props {
  children: ReactNode;
  fallback?: (error: Error, reset: () => void) => ReactNode;
}

interface State {
  error: Error | null;
}

/**
 * App-wide error boundary. Wraps the layout's <Outlet /> so that a broken
 * render in any page falls back to a recoverable fallback UI without
 * corrupting the router. Has a "Try again" action that resets state and
 * re-renders the subtree.
 */
export class ErrorBoundary extends Component<Props, State> {
  override state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  override componentDidCatch(error: Error, info: ErrorInfo): void {
    logger.error("error_boundary", { message: error.message, stack: info.componentStack });
  }

  reset = (): void => {
    this.setState({ error: null });
  };

  override render(): ReactNode {
    const { error } = this.state;
    if (!error) return this.props.children;
    if (this.props.fallback) return this.props.fallback(error, this.reset);
    return (
      <div role="alert" className="max-w-xl mx-auto my-16 p-6 card border border-red-200 bg-red-50">
        <h2 className="font-display text-sub text-red-800 mb-2">Something went wrong.</h2>
        <p className="text-caption text-red-900/80 mb-4">
          An unexpected error crashed this page. You can try again; if it persists, reload.
        </p>
        <details className="text-caption text-red-900/70 mb-4">
          <summary className="cursor-pointer">Details</summary>
          <pre className="whitespace-pre-wrap mt-2 text-[11px]">{error.message}</pre>
        </details>
        <button
          onClick={this.reset}
          className="button button-primary focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-red-400"
        >
          Try again
        </button>
      </div>
    );
  }
}

export default ErrorBoundary;
