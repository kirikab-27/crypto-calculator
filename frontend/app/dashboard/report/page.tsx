"use client";

import { useState } from "react";
import axios from "axios";

interface Transaction {
  date: string;
  type: "buy" | "sell";
  currency: string;
  amount: number;
  price: number;
  fee: number;
}

export default function Report() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [reportContent, setReportContent] = useState("");
  const [method, setMethod] = useState<"fifo" | "lifo">("fifo");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const generateReport = async () => {
    setLoading(true);
    setError("");
    setReportContent("");

    try {
      // For demo purposes, using sample transactions
      // In production, you would fetch user's actual transactions
      const sampleTransactions: Transaction[] = [
        { date: "2024-01-01", type: "buy", currency: "BTC", amount: 0.5, price: 30000, fee: 10 },
        { date: "2024-02-01", type: "buy", currency: "BTC", amount: 0.3, price: 35000, fee: 10 },
        { date: "2024-03-01", type: "sell", currency: "BTC", amount: 0.4, price: 40000, fee: 10 },
      ];

      const response = await axios.post("/api/generate-report", {
        transactions: sampleTransactions,
        method,
      });

      setReportContent(response.data.content);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Report generation failed");
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = () => {
    if (!reportContent) return;

    const blob = new Blob([reportContent], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `crypto_report_${new Date().toISOString().split("T")[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="px-4 sm:px-0">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-semibold text-gray-900">
            Generate Report
          </h1>
          <p className="mt-2 text-sm text-gray-700">
            Generate tax reports and transaction summaries
          </p>
        </div>
      </div>

      <div className="mt-8 bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="space-y-6">
            {/* Report Options */}
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Calculation Method
                </label>
                <select
                  value={method}
                  onChange={(e) => setMethod(e.target.value as "fifo" | "lifo")}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                >
                  <option value="fifo">FIFO (First In, First Out)</option>
                  <option value="lifo">LIFO (Last In, First Out)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Start Date
                </label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  End Date
                </label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
              </div>
            </div>

            {/* Report Types */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Report Type
              </label>
              <div className="space-y-4">
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="report-type"
                    value="summary"
                    defaultChecked
                    className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300"
                  />
                  <span className="ml-3">
                    <span className="block text-sm font-medium text-gray-700">
                      Tax Summary Report
                    </span>
                    <span className="block text-sm text-gray-500">
                      Summary of gains/losses for tax purposes
                    </span>
                  </span>
                </label>

                <label className="flex items-center">
                  <input
                    type="radio"
                    name="report-type"
                    value="detailed"
                    className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300"
                  />
                  <span className="ml-3">
                    <span className="block text-sm font-medium text-gray-700">
                      Detailed Transaction Report
                    </span>
                    <span className="block text-sm text-gray-500">
                      All transactions with calculated gains/losses
                    </span>
                  </span>
                </label>

                <label className="flex items-center">
                  <input
                    type="radio"
                    name="report-type"
                    value="inventory"
                    className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300"
                  />
                  <span className="ml-3">
                    <span className="block text-sm font-medium text-gray-700">
                      Inventory Report
                    </span>
                    <span className="block text-sm text-gray-500">
                      Current holdings and cost basis
                    </span>
                  </span>
                </label>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="rounded-md bg-red-50 p-4">
                <div className="text-sm text-red-800">{error}</div>
              </div>
            )}

            {/* Generate Button */}
            <div className="flex justify-end">
              <button
                onClick={generateReport}
                disabled={loading}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
              >
                {loading ? "Generating..." : "Generate Report"}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Report Preview */}
      {reportContent && (
        <div className="mt-8 bg-white shadow sm:rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <div className="sm:flex sm:items-center sm:justify-between mb-4">
              <h3 className="text-lg font-medium leading-6 text-gray-900">
                Report Preview
              </h3>
              <button
                onClick={downloadReport}
                className="mt-3 sm:mt-0 inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                <svg
                  className="-ml-1 mr-2 h-5 w-5 text-gray-500"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  aria-hidden="true"
                >
                  <path
                    fillRule="evenodd"
                    d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
                Download CSV
              </button>
            </div>
            <pre className="bg-gray-50 p-4 rounded-md text-xs overflow-x-auto">
              {reportContent}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}