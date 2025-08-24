import React from 'react';

const ErrorMessage = ({ message, onDismiss }) => {
  return (
    <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg p-4 flex items-center justify-between animate-fade-in">
      <span className="text-sm font-medium">{message}</span>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="ml-4 text-red-600 hover:text-red-800"
        >
          ✕
        </button>
      )}
    </div>
  );
};

export default ErrorMessage;