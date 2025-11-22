import { Component } from 'react';

class ComponentErrorBoundary extends Component {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error) {
    console.error(`Error in ${this.props.componentName}:`, error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 border border-red-300 bg-red-50 rounded-lg">
          <p className="text-red-800 font-medium">Component Error: {this.props.componentName}</p>
          <p className="text-red-600 text-sm">Check browser console for details</p>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ComponentErrorBoundary;