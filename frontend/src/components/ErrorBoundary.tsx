import { Component, ErrorInfo, ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen w-full bg-white flex items-center justify-center p-6">
          <div className="max-w-md w-full bg-red-50 rounded-3xl shadow-2xl border-2 border-red-200 p-8 text-center">
            <div className="text-6xl mb-4">⚠️</div>
            <h1 className="text-2xl font-bold text-red-900 mb-3">Something went wrong</h1>
            <p className="text-red-700 mb-6">
              We encountered an unexpected error. Please refresh the page to continue.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-red-600 to-red-700 text-white font-semibold hover:shadow-lg transition-all"
            >
              Refresh Page
            </button>
            {import.meta.env.DEV && this.state.error && (
              <details className="mt-6 text-left">
                <summary className="cursor-pointer text-sm text-red-600 font-medium">
                  Error Details (Dev Only)
                </summary>
                <pre className="mt-2 text-xs bg-red-100 p-3 rounded overflow-auto">
                  {this.state.error.toString()}
                </pre>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
