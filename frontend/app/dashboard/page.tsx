"use client";

import { useState, useEffect } from "react";
import axios from "axios";

interface Transaction {
  id?: number;
  date: string;
  type: "buy" | "sell";
  currency: string;
  amount: number;
  price: number;
  fee: number;
  gain_loss?: number;
}

interface Summary {
  total_realized_gains: number;
  total_realized_losses: number;
  net_gain_loss: number;
  transactions_count: number;
}

export default function Dashboard() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [method, setMethod] = useState<"fifo" | "lifo">("fifo");
  const [summary, setSummary] = useState<Summary | null>(null);
  const [inventory, setInventory] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Form state
  const [date, setDate] = useState("");
  const [type, setType] = useState<"buy" | "sell">("buy");
  const [currency, setCurrency] = useState("");
  const [amount, setAmount] = useState("");
  const [price, setPrice] = useState("");
  const [fee, setFee] = useState("0");

  // Load transactions from database on component mount
  useEffect(() => {
    const loadTransactions = async () => {
      try {
        const response = await axios.get("/api/transactions");
        setTransactions(response.data);
      } catch (err: any) {
        console.error("Failed to load transactions:", err);
        if (err.code === 'ERR_NETWORK' || err.response?.status === 404) {
          setError("Backend server is not running. Please start the backend server on port 8000. Run './run_dev.sh' (Unix/Mac) or 'run_dev.bat' (Windows) from the project root.");
        }
      }
    };
    loadTransactions();
  }, []);

  const addTransaction = async () => {
    if (!date || !currency || !amount || !price) {
      setError("Please fill all required fields");
      return;
    }

    const newTransaction: Transaction = {
      date,
      type,
      currency: currency.toUpperCase(),
      amount: parseFloat(amount),
      price: parseFloat(price),
      fee: parseFloat(fee) || 0,
    };

    try {
      // Save to database
      const response = await axios.post("/api/transactions", newTransaction);
      const savedTransaction = response.data;
      
      // Add to local state with the ID from the database
      setTransactions([...transactions, savedTransaction]);
      
      // Reset form
      setDate("");
      setCurrency("");
      setAmount("");
      setPrice("");
      setFee("0");
      setError("");
    } catch (err: any) {
      if (err.code === 'ERR_NETWORK' || err.response?.status === 404) {
        setError("Backend server is not running. Please start the backend server on port 8000.");
      } else {
        setError(err.response?.data?.detail || "Failed to save transaction");
      }
    }
  };

  const removeTransaction = async (index: number) => {
    const transaction = transactions[index];
    
    try {
      // If transaction has an ID, delete from database
      if (transaction.id) {
        await axios.delete(`/api/transactions/${transaction.id}`);
      }
      
      // Remove from local state
      setTransactions(transactions.filter((_, i) => i !== index));
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to delete transaction");
    }
  };

  const calculate = async () => {
    if (transactions.length === 0) {
      setError("Please add at least one transaction");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await axios.post("/api/calculate", {
        transactions,
        method,
      });

      setSummary(response.data.summary);
      setInventory(response.data.inventory);
      
      // Update transactions with gain/loss data and save to database
      const updatedTransactions = await Promise.all(
        transactions.map(async (tx, index) => {
          const apiTx = response.data.transactions[index];
          const updatedTx = {
            ...tx,
            gain_loss: apiTx?.gain_loss,
          };
          
          // Update in database if transaction has an ID
          if (tx.id && apiTx?.gain_loss !== undefined) {
            try {
              const updateResponse = await axios.post("/api/transactions", updatedTx);
              return updateResponse.data;
            } catch (err) {
              console.error("Failed to update transaction gain/loss:", err);
              return updatedTx;
            }
          }
          
          return updatedTx;
        })
      );
      setTransactions(updatedTransactions);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Calculation failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="px-4 sm:px-0">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-semibold text-gray-900">
            Crypto Calculator
          </h1>
          <p className="mt-2 text-sm text-gray-700">
            Add your cryptocurrency transactions to calculate gains and losses
          </p>
        </div>
      </div>

      {/* Transaction Form */}
      <div className="mt-8 bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">
            Add Transaction
          </h3>
          <div className="grid grid-cols-6 gap-6">
            <div className="col-span-6 sm:col-span-1">
              <label className="block text-sm font-medium text-gray-700">
                Date
              </label>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              />
            </div>

            <div className="col-span-6 sm:col-span-1">
              <label className="block text-sm font-medium text-gray-700">
                Type
              </label>
              <select
                value={type}
                onChange={(e) => setType(e.target.value as "buy" | "sell")}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              >
                <option value="buy">Buy</option>
                <option value="sell">Sell</option>
              </select>
            </div>

            <div className="col-span-6 sm:col-span-1">
              <label className="block text-sm font-medium text-gray-700">
                Currency
              </label>
              <input
                type="text"
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                placeholder="BTC"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              />
            </div>

            <div className="col-span-6 sm:col-span-1">
              <label className="block text-sm font-medium text-gray-700">
                Amount
              </label>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                step="0.00000001"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              />
            </div>

            <div className="col-span-6 sm:col-span-1">
              <label className="block text-sm font-medium text-gray-700">
                Price (USD)
              </label>
              <input
                type="number"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                step="0.01"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              />
            </div>

            <div className="col-span-6 sm:col-span-1">
              <label className="block text-sm font-medium text-gray-700">
                Fee (USD)
              </label>
              <input
                type="number"
                value={fee}
                onChange={(e) => setFee(e.target.value)}
                step="0.01"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              />
            </div>
          </div>

          {error && (
            <div className="mt-4 rounded-md bg-red-50 p-4">
              <div className="text-sm text-red-800">{error}</div>
            </div>
          )}

          <div className="mt-5">
            <button
              onClick={addTransaction}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Add Transaction
            </button>
          </div>
        </div>
      </div>

      {/* Transactions Table */}
      {transactions.length > 0 && (
        <div className="mt-8 bg-white shadow sm:rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">
              Transactions
            </h3>
            <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
              <table className="min-w-full divide-y divide-gray-300">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                      Date
                    </th>
                    <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                      Type
                    </th>
                    <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                      Currency
                    </th>
                    <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                      Amount
                    </th>
                    <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                      Price
                    </th>
                    <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                      Fee
                    </th>
                    <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                      Gain/Loss
                    </th>
                    <th className="relative py-3.5 pl-3 pr-4 sm:pr-6">
                      <span className="sr-only">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {transactions.map((tx, index) => (
                    <tr key={index}>
                      <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-900">
                        {tx.date}
                      </td>
                      <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-900">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            tx.type === "buy"
                              ? "bg-green-100 text-green-800"
                              : "bg-red-100 text-red-800"
                          }`}
                        >
                          {tx.type.toUpperCase()}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-900">
                        {tx.currency}
                      </td>
                      <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-900">
                        {tx.amount}
                      </td>
                      <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-900">
                        ${tx.price.toFixed(2)}
                      </td>
                      <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-900">
                        ${tx.fee.toFixed(2)}
                      </td>
                      <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-900">
                        {tx.gain_loss !== undefined && tx.gain_loss !== null && (
                          <span
                            className={
                              tx.gain_loss >= 0
                                ? "text-green-600"
                                : "text-red-600"
                            }
                          >
                            ${tx.gain_loss.toFixed(2)}
                          </span>
                        )}
                      </td>
                      <td className="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-6">
                        <button
                          onClick={() => removeTransaction(index)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Remove
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Calculation Options */}
            <div className="mt-6 flex items-center justify-between">
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

              <button
                onClick={calculate}
                disabled={loading}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
              >
                {loading ? "Calculating..." : "Calculate Gains/Losses"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Summary */}
      {summary && (
        <div className="mt-8 bg-white shadow sm:rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">
              Summary
            </h3>
            <dl className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-3">
              <div className="px-4 py-5 bg-gray-50 shadow rounded-lg overflow-hidden sm:p-6">
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Total Realized Gains
                </dt>
                <dd className="mt-1 text-3xl font-semibold text-green-600">
                  ${(summary.total_realized_gains ?? 0).toFixed(2)}
                </dd>
              </div>
              <div className="px-4 py-5 bg-gray-50 shadow rounded-lg overflow-hidden sm:p-6">
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Total Realized Losses
                </dt>
                <dd className="mt-1 text-3xl font-semibold text-red-600">
                  ${Math.abs(summary.total_realized_losses ?? 0).toFixed(2)}
                </dd>
              </div>
              <div className="px-4 py-5 bg-gray-50 shadow rounded-lg overflow-hidden sm:p-6">
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Net Gain/Loss
                </dt>
                <dd
                  className={`mt-1 text-3xl font-semibold ${
                    (summary.net_gain_loss ?? 0) >= 0
                      ? "text-green-600"
                      : "text-red-600"
                  }`}
                >
                  ${(summary.net_gain_loss ?? 0).toFixed(2)}
                </dd>
              </div>
            </dl>

            {/* Inventory Status */}
            {inventory && Object.keys(inventory).length > 0 && (
              <div className="mt-6">
                <h4 className="text-md font-medium text-gray-900 mb-3">
                  Current Inventory
                </h4>
                <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
                  <table className="min-w-full divide-y divide-gray-300">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                          Currency
                        </th>
                        <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                          Total Amount
                        </th>
                        <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                          Average Price
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 bg-white">
                      {Object.entries(inventory).map(([currency, data]: [string, any]) => (
                        <tr key={currency}>
                          <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-900">
                            {currency}
                          </td>
                          <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-900">
                            {data.total_amount}
                          </td>
                          <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-900">
                            ${(data.average_price ?? 0).toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}