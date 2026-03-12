'use client';

import { AlertCircle, RefreshCw, MapPin } from 'lucide-react';

interface ApiErrorProps {
  error: any;
  message?: string;
  onRetry?: () => void;
}

export function ApiError({ error, message, onRetry }: ApiErrorProps) {
  const errorMessage = message || error?.message || 'Failed to load data';
  const is404 = error?.status === 404;
  const is502 = error?.status === 502 || error?.status === 503 || error?.status === 504;
  const isTimeout = errorMessage.includes('timeout') || errorMessage.includes('timed out');
  const isNetwork = errorMessage.includes('network') || errorMessage.includes('fetch');

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-8 text-center">
      <div className="inline-flex items-center justify-center w-16 h-16 bg-amber-100 dark:bg-amber-900/30 rounded-full mb-4">
        {is404 ? (
          <MapPin className="w-8 h-8 text-amber-600" />
        ) : (
          <AlertCircle className="w-8 h-8 text-amber-600 dark:text-amber-400" />
        )}
      </div>
      
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
        {is404 ? 'No Data Available' : is502 ? 'Server is Starting Up' : isTimeout ? 'Request Timeout' : 'Unable to Load Data'}
      </h3>
      
      <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-md mx-auto">
        {is404 ? (
          'Building data is not available for this airport. We currently have data for airports in CA, TX, FL, AZ, IL, GA, and CO.'
        ) : is502 ? (
          'The API server is waking up from sleep — this takes 20–50 seconds on the free tier. Click "Try Again" in a moment, or wait and the page will retry automatically.'
        ) : isTimeout ? (
          'The request took too long to complete. The airport may have a large number of buildings. Try reducing the search radius or increasing the minimum building size.'
        ) : isNetwork ? (
          'Could not connect to the server. Please check your internet connection and try again.'
        ) : (
          errorMessage
        )}
      </p>
      
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Try Again
        </button>
      )}
      
      {is404 && (
        <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-sm text-left max-w-md mx-auto">
          <p className="font-medium text-blue-900 dark:text-blue-200 mb-1">Supported Airports:</p>
          <p className="text-blue-700 dark:text-blue-300">
            All 30 major US airports are supported. Select an airport from the dropdown above.
          </p>
        </div>
      )}
    </div>
  );
}
