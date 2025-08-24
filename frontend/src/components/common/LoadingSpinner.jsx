import React from 'react';

const LoadingSpinner = ({ message = 'Loading...' }) => {
  return (
    <div className="flex flex-col items-center justify-center p-8 space-y-4">
      <div className="w-10 h-10 animate-spin">
        <div className="w-full h-full border-4 border-gray-200 border-t-primary-600 rounded-full"></div>
      </div>
      <p className="text-gray-600 text-center font-medium">{message}</p>
    </div>
  );
};

export default LoadingSpinner;