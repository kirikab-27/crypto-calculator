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

interface TaxSummaryData {
  report_period_start: string;
  report_period_end: string;
  creation_date: string;
  calculation_method: string;
  total_realized_profit: number;
  total_realized_loss: number;
  net_profit_loss: number;
  total_fees: number;
  currency_breakdown: Record<string, any>;
  monthly_breakdown: Record<string, any>;
  quarterly_breakdown: Record<string, any>;
  total_buy_transactions: number;
  total_sell_transactions: number;
  total_buy_amount: number;
  total_sell_amount: number;
  current_holdings: Record<string, any>;
  taxable_income: number;
  loss_carryforward: number;
  sell_transactions: any[];
}

// Component to display formatted tax summary
function TaxSummaryDisplay({ data }: { data: TaxSummaryData }) {
  return (
    <div className="space-y-6 text-sm">
      {/* Basic Information */}
      <div>
        <h4 className="font-semibold mb-2">基本情報</h4>
        <div className="grid grid-cols-2 gap-2">
          <div>レポート期間:</div>
          <div>{data.report_period_start} 〜 {data.report_period_end}</div>
          <div>作成日時:</div>
          <div>{data.creation_date}</div>
          <div>計算方法:</div>
          <div>{data.calculation_method}</div>
        </div>
      </div>

      {/* Profit/Loss Summary */}
      <div>
        <h4 className="font-semibold mb-2">損益サマリー</h4>
        <div className="grid grid-cols-2 gap-2">
          <div>総実現利益:</div>
          <div>¥{data.total_realized_profit.toLocaleString()}</div>
          <div>総実現損失:</div>
          <div>¥{data.total_realized_loss.toLocaleString()}</div>
          <div>純損益:</div>
          <div className={data.net_profit_loss >= 0 ? "text-green-600" : "text-red-600"}>
            ¥{data.net_profit_loss.toLocaleString()}
          </div>
          <div>総取引手数料:</div>
          <div>¥{data.total_fees.toLocaleString()}</div>
        </div>
      </div>

      {/* Currency Breakdown */}
      {Object.keys(data.currency_breakdown).length > 0 && (
        <div>
          <h4 className="font-semibold mb-2">通貨別損益</h4>
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">通貨</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">純損益</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">売却数量</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(data.currency_breakdown).map(([currency, stats]: [string, any]) => (
                <tr key={currency}>
                  <td className="px-3 py-2">{currency}</td>
                  <td className={`px-3 py-2 ${stats.net_profit_loss >= 0 ? "text-green-600" : "text-red-600"}`}>
                    ¥{stats.net_profit_loss.toLocaleString()}
                  </td>
                  <td className="px-3 py-2">{stats.sell_quantity.toFixed(8)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Tax Information */}
      <div>
        <h4 className="font-semibold mb-2">税務関連情報</h4>
        <div className="grid grid-cols-2 gap-2">
          <div>課税対象所得:</div>
          <div>¥{data.taxable_income.toLocaleString()}</div>
          <div>損失繰越可能額:</div>
          <div>¥{data.loss_carryforward.toLocaleString()}</div>
        </div>
      </div>
    </div>
  );
}

export default function Report() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [reportContent, setReportContent] = useState("");
  const [reportData, setReportData] = useState<TaxSummaryData | null>(null);
  const [method, setMethod] = useState<"FIFO" | "LIFO">("FIFO");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [reportType, setReportType] = useState("summary");
  const [format, setFormat] = useState<"json" | "csv" | "pdf">("json");

  const generateReport = async () => {
    setLoading(true);
    setError("");
    setReportContent("");
    setReportData(null);

    try {
      const token = localStorage.getItem("token");
      if (!token) {
        throw new Error("Authentication required");
      }

      // Determine which endpoint to use based on report type
      if (reportType === "summary") {
        // Use the new tax summary report endpoint
        const response = await axios.post(
          "/api/tax-summary-report",
          {
            method,
            start_date: startDate || undefined,
            end_date: endDate || undefined,
            format,
          },
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (format === "json") {
          setReportData(response.data.content);
          setReportContent(JSON.stringify(response.data.content, null, 2));
        } else {
          setReportContent(response.data.content);
        }
      } else {
        // Use the existing endpoint for other report types
        const transactionsResponse = await axios.get("/api/transactions", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        const response = await axios.post(
          "/api/generate-report",
          {
            transactions: transactionsResponse.data,
            method: method.toLowerCase(),
          },
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        setReportContent(response.data.content);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Report generation failed");
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = () => {
    if (!reportContent) return;

    let mimeType = "text/csv";
    let extension = "csv";
    let content: any = reportContent;

    if (format === "json") {
      mimeType = "application/json";
      extension = "json";
    } else if (format === "pdf") {
      // PDF is base64 encoded
      const byteCharacters = atob(reportContent);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      content = byteArray;
      mimeType = "application/pdf";
      extension = "pdf";
    }

    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `tax_summary_report_${new Date().toISOString().split("T")[0]}.${extension}`;
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
                  onChange={(e) => setMethod(e.target.value as "FIFO" | "LIFO")}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                >
                  <option value="FIFO">FIFO (先入先出法)</option>
                  <option value="LIFO">LIFO (後入先出法)</option>
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
                    checked={reportType === "summary"}
                    onChange={(e) => setReportType(e.target.value)}
                    className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300"
                  />
                  <span className="ml-3">
                    <span className="block text-sm font-medium text-gray-700">
                      税務サマリーレポート
                    </span>
                    <span className="block text-sm text-gray-500">
                      確定申告用の包括的な損益サマリー
                    </span>
                  </span>
                </label>

                <label className="flex items-center">
                  <input
                    type="radio"
                    name="report-type"
                    value="detailed"
                    checked={reportType === "detailed"}
                    onChange={(e) => setReportType(e.target.value)}
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
                    checked={reportType === "inventory"}
                    onChange={(e) => setReportType(e.target.value)}
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

            {/* Format Selection for Tax Summary */}
            {reportType === "summary" && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Export Format
                </label>
                <div className="space-x-4">
                  <label className="inline-flex items-center">
                    <input
                      type="radio"
                      name="format"
                      value="json"
                      checked={format === "json"}
                      onChange={(e) => setFormat(e.target.value as "json" | "csv" | "pdf")}
                      className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300"
                    />
                    <span className="ml-2 text-sm text-gray-700">JSON</span>
                  </label>
                  <label className="inline-flex items-center">
                    <input
                      type="radio"
                      name="format"
                      value="csv"
                      checked={format === "csv"}
                      onChange={(e) => setFormat(e.target.value as "json" | "csv" | "pdf")}
                      className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300"
                    />
                    <span className="ml-2 text-sm text-gray-700">CSV</span>
                  </label>
                  <label className="inline-flex items-center">
                    <input
                      type="radio"
                      name="format"
                      value="pdf"
                      checked={format === "pdf"}
                      onChange={(e) => setFormat(e.target.value as "json" | "csv" | "pdf")}
                      className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300"
                    />
                    <span className="ml-2 text-sm text-gray-700">PDF</span>
                  </label>
                </div>
              </div>
            )}

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
                Download {format.toUpperCase()}
              </button>
            </div>
            {format === "json" && reportData ? (
              <div className="bg-gray-50 p-4 rounded-md overflow-x-auto">
                <TaxSummaryDisplay data={reportData} />
              </div>
            ) : (
              <pre className="bg-gray-50 p-4 rounded-md text-xs overflow-x-auto">
                {reportContent}
              </pre>
            )}
          </div>
        </div>
      )}
    </div>
  );
}