"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";

export default function ImportCSV() {
  const router = useRouter();
  const [source, setSource] = useState("generic");
  const [csvContent, setCsvContent] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      const reader = new FileReader();
      reader.onload = (event) => {
        setCsvContent(event.target?.result as string);
      };
      reader.readAsText(selectedFile);
    }
  };

  const handleImport = async () => {
    if (!csvContent) {
      setError("Please select a CSV file");
      return;
    }

    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const response = await axios.post("/api/import-csv", {
        content: csvContent,
        source,
      });

      setSuccess(response.data.message);
      
      // Redirect to calculator after 2 seconds
      setTimeout(() => {
        router.push("/dashboard");
      }, 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Import failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="px-4 sm:px-0">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-semibold text-gray-900">
            Import CSV
          </h1>
          <p className="mt-2 text-sm text-gray-700">
            Import transaction data from CSV files exported by exchanges
          </p>
        </div>
      </div>

      <div className="mt-8 bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="space-y-6">
            {/* Source Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Data Source
              </label>
              <select
                value={source}
                onChange={(e) => setSource(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              >
                <option value="generic">Generic CSV</option>
                <option value="binance">Binance</option>
                <option value="mexc">MEXC</option>
              </select>
              <p className="mt-2 text-sm text-gray-500">
                Select the exchange or use generic format for custom CSV files
              </p>
            </div>

            {/* CSV Format Help */}
            <div className="rounded-md bg-blue-50 p-4">
              <div className="flex">
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-blue-800">
                    CSV Format
                  </h3>
                  <div className="mt-2 text-sm text-blue-700">
                    <p>For generic CSV, use the following columns:</p>
                    <ul className="list-disc list-inside mt-1">
                      <li>date (YYYY-MM-DD)</li>
                      <li>type (buy/sell)</li>
                      <li>currency (BTC, ETH, etc.)</li>
                      <li>amount</li>
                      <li>price</li>
                      <li>fee (optional)</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            {/* File Upload */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Select CSV File
              </label>
              <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                <div className="space-y-1 text-center">
                  <svg
                    className="mx-auto h-12 w-12 text-gray-400"
                    stroke="currentColor"
                    fill="none"
                    viewBox="0 0 48 48"
                    aria-hidden="true"
                  >
                    <path
                      d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                      strokeWidth={2}
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                  <div className="flex text-sm text-gray-600">
                    <label
                      htmlFor="file-upload"
                      className="relative cursor-pointer bg-white rounded-md font-medium text-indigo-600 hover:text-indigo-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500"
                    >
                      <span>Upload a file</span>
                      <input
                        id="file-upload"
                        name="file-upload"
                        type="file"
                        accept=".csv"
                        className="sr-only"
                        onChange={handleFileChange}
                      />
                    </label>
                    <p className="pl-1">or drag and drop</p>
                  </div>
                  <p className="text-xs text-gray-500">CSV files only</p>
                </div>
              </div>
              {file && (
                <p className="mt-2 text-sm text-gray-600">
                  Selected: {file.name}
                </p>
              )}
            </div>

            {/* CSV Preview */}
            {csvContent && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  CSV Preview (first 10 lines)
                </label>
                <pre className="bg-gray-50 p-4 rounded-md text-xs overflow-x-auto">
                  {csvContent.split('\n').slice(0, 10).join('\n')}
                  {csvContent.split('\n').length > 10 && '\n...'}
                </pre>
              </div>
            )}

            {/* Error/Success Messages */}
            {error && (
              <div className="rounded-md bg-red-50 p-4">
                <div className="text-sm text-red-800">{error}</div>
              </div>
            )}

            {success && (
              <div className="rounded-md bg-green-50 p-4">
                <div className="text-sm text-green-800">{success}</div>
              </div>
            )}

            {/* Import Button */}
            <div className="flex justify-end">
              <button
                onClick={handleImport}
                disabled={loading || !csvContent}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
              >
                {loading ? "Importing..." : "Import Transactions"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}