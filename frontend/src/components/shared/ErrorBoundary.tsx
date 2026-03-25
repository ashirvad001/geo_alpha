"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";
import { AlertCircle, RefreshCcw } from "lucide-react";

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(_: Error): State {
    return { hasError: true };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center p-12 bg-card rounded-3xl border border-white/5 text-center space-y-4">
          <AlertCircle size={48} className="text-risk-high" />
          <h2 className="text-xl font-bold text-white">Something went wrong</h2>
          <p className="text-white/40 text-sm max-w-xs mx-auto">
            The data stream encountered a disruption. Our intelligence monitors have been notified.
          </p>
          <button
            onClick={() => this.setState({ hasError: false })}
            className="flex items-center gap-2 px-6 py-2 bg-white/5 hover:bg-white/10 rounded-xl text-xs font-bold transition-all"
          >
            <RefreshCcw size={14} /> Retry Terminal
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
