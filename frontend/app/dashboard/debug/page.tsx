"use client";

import { useState } from "react";
import axios from "axios";
import { redirect } from "next/navigation";

export default function DateFilterDebug() {
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [debugInfo, setDebugInfo] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const runDebug = async () => {
    setLoading(true);
    setError("");
    setDebugInfo(null);

    try {
      const params = new URLSearchParams();
      if (startDate) params.append("start_date", startDate);
      if (endDate) params.append("end_date", endDate);

      const response = await axios.get(`/api/debug/date-filter?${params}`);
      setDebugInfo(response.data);
    } catch (err: any) {
      if (err.response?.status === 401) {
        redirect("/login");
      } else {
        setError(err.response?.data?.detail || "Failed to run debug");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Date Filter Debug Tool</h1>
      
      <div className="bg-white p-6 rounded-lg shadow mb-6">
        <h2 className="text-lg font-semibold mb-4">Test Date Filtering</h2>
        
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium mb-1">Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 border rounded-md"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 border rounded-md"
            />
          </div>
        </div>
        
        <button
          onClick={runDebug}
          disabled={loading}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:opacity-50"
        >
          {loading ? "Running Debug..." : "Run Debug"}
        </button>
      </div>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}
      
      {debugInfo && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">Debug Results</h2>
          
          <div className="space-y-4">
            <div>
              <h3 className="font-medium">Input Values</h3>
              <pre className="bg-gray-100 p-2 rounded text-sm">
                {JSON.stringify(debugInfo.input, null, 2)}
              </pre>
            </div>
            
            <div>
              <h3 className="font-medium">Normalized Values</h3>
              <pre className="bg-gray-100 p-2 rounded text-sm">
                {JSON.stringify(debugInfo.normalized, null, 2)}
              </pre>
            </div>
            
            <div>
              <h3 className="font-medium">Validation</h3>
              <pre className="bg-gray-100 p-2 rounded text-sm">
                {JSON.stringify(debugInfo.validation, null, 2)}
              </pre>
            </div>
            
            {debugInfo.errors && debugInfo.errors.length > 0 && (
              <div>
                <h3 className="font-medium text-red-600">Errors</h3>
                <ul className="list-disc list-inside text-red-600">
                  {debugInfo.errors.map((err: string, i: number) => (
                    <li key={i}>{err}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {debugInfo.filter_result && (
              <div>
                <h3 className="font-medium">Filter Result</h3>
                <pre className="bg-gray-100 p-2 rounded text-sm">
                  {JSON.stringify(debugInfo.filter_result, null, 2)}
                </pre>
              </div>
            )}
            
            {debugInfo.sample_dates_in_db && (
              <div>
                <h3 className="font-medium">Sample Dates in Database</h3>
                <div className="bg-gray-100 p-2 rounded">
                  {debugInfo.sample_dates_in_db.length > 0 ? (
                    <ul className="list-disc list-inside">
                      {debugInfo.sample_dates_in_db.map((date: string, i: number) => (
                        <li key={i}>{date}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-gray-500">No transactions found</p>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}