"use client";

import { useState, useEffect, useMemo, useCallback, Component, ReactNode } from "react";
import axios from "axios";
import { debounce } from "lodash";

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

// Error Boundary Component
interface ErrorBoundaryState {
  hasError: boolean;
}

class DateFilterErrorBoundary extends Component<{ children: ReactNode }, ErrorBoundaryState> {
  state = { hasError: false };
  
  static getDerivedStateFromError(error: Error) {
    return { hasError: true };
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div className="text-red-600 p-4 bg-red-50 rounded-md">
          日付フィルタで問題が発生しました。ページを再読み込みしてください。
        </div>
      );
    }
    return this.props.children;
  }
}

export default function Dashboard() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [method, setMethod] = useState<"fifo" | "lifo">("fifo");
  const [summary, setSummary] = useState<Summary | null>(null);
  const [inventory, setInventory] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Pagination and filter state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [totalItems, setTotalItems] = useState(0);
  const [typeFilter, setTypeFilter] = useState<"buy" | "sell" | "both">("both");
  const [currencyFilter, setCurrencyFilter] = useState("");
  const [availableCurrencies, setAvailableCurrencies] = useState<string[]>([]);
  const [startDateFilter, setStartDateFilter] = useState("");
  const [endDateFilter, setEndDateFilter] = useState("");

  // Form state
  const [date, setDate] = useState("");
  const [type, setType] = useState<"buy" | "sell">("buy");
  const [currency, setCurrency] = useState("");
  const [amount, setAmount] = useState("");
  const [price, setPrice] = useState("");
  const [fee, setFee] = useState("0");
  const [totalValue, setTotalValue] = useState("0.00");

  // Edit state
  const [editingTransaction, setEditingTransaction] = useState<Transaction | null>(null);
  const [editDate, setEditDate] = useState("");
  const [editType, setEditType] = useState<"buy" | "sell">("buy");
  const [editCurrency, setEditCurrency] = useState("");
  const [editAmount, setEditAmount] = useState("");
  const [editPrice, setEditPrice] = useState("");
  const [editFee, setEditFee] = useState("0");
  
  // State for preventing duplicate submissions
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // State to force reload data
  const [forceReload, setForceReload] = useState(0);
  
  // Date validation state
  const [dateValidationError, setDateValidationError] = useState<string | null>(null);
  
  // Loading state for date filtering
  const [isFilterLoading, setIsFilterLoading] = useState(false);

  // Calculate total value when amount or price changes
  useEffect(() => {
    const amountNum = parseFloat(amount) || 0;
    const priceNum = parseFloat(price) || 0;
    const total = amountNum * priceNum;
    setTotalValue(total.toFixed(2));
  }, [amount, price]);

  // Date validation function
  const validateDateRange = (start: string, end: string): string | null => {
    if (!start || !end) return null;
    
    const startDate = new Date(start);
    const endDate = new Date(end);
    const today = new Date();
    
    if (startDate > endDate) return "開始日は終了日より前にしてください";
    if (endDate > today) return "終了日は今日以前の日付にしてください";
    if (startDate < new Date('2020-01-01')) return "2020年以降の日付を選択してください";
    
    return null;
  };

  // Validate dates whenever they change
  useEffect(() => {
    const error = validateDateRange(startDateFilter, endDateFilter);
    setDateValidationError(error);
  }, [startDateFilter, endDateFilter]);

  // URL parameter synchronization
  useEffect(() => {
    const params = new URLSearchParams();
    if (startDateFilter) params.set('start', startDateFilter);
    if (endDateFilter) params.set('end', endDateFilter);
    if (typeFilter !== 'both') params.set('type', typeFilter);
    if (currencyFilter) params.set('currency', currencyFilter);
    
    const newUrl = `${window.location.pathname}?${params.toString()}`;
    window.history.replaceState({}, '', newUrl);
  }, [startDateFilter, endDateFilter, typeFilter, currencyFilter]);

  // Load filters from URL on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const start = params.get('start');
    const end = params.get('end');
    const type = params.get('type');
    const currency = params.get('currency');
    
    if (start) setStartDateFilter(start);
    if (end) setEndDateFilter(end);
    if (type && (type === 'buy' || type === 'sell')) setTypeFilter(type);
    if (currency) setCurrencyFilter(currency);
  }, []);

  // Create debounced filter function
  const debouncedLoadTransactions = useMemo(
    () => debounce(async () => {
      if (dateValidationError) {
        setTransactions([]);
        setTotalItems(0);
        return;
      }
      
      setIsFilterLoading(true);
      try {
        // Log the current filter state
        console.log('[Frontend Debug] Current filter state:', {
          startDateFilter,
          endDateFilter,
          typeFilter,
          currencyFilter,
          currentPage,
          itemsPerPage
        });
        
        const offset = (currentPage - 1) * itemsPerPage;
        const params = new URLSearchParams({
          limit: itemsPerPage.toString(),
          offset: offset.toString()
        });
        
        if (typeFilter !== "both") {
          params.append("type", typeFilter);
        }
        
        if (currencyFilter) {
          params.append("currency", currencyFilter);
        }
        
        if (startDateFilter) {
          params.append("start_date", startDateFilter);
        }
        
        if (endDateFilter) {
          params.append("end_date", endDateFilter);
        }
        
        // Debug logging for date filter issue
        console.log('[Frontend Debug] Filter params:', {
          startDate: startDateFilter,
          endDate: endDateFilter,
          queryString: params.toString(),
          url: `/api/transactions/filtered?${params}`,
          allParams: Array.from(params.entries())
        });
        
        // Also log to help users debug
        if (startDateFilter || endDateFilter) {
          console.log('[Date Filter Active]', {
            startDate: startDateFilter || '(none)',
            endDate: endDateFilter || '(none)',
            expectedBehavior: 'Transactions should be filtered to show only those within the date range (inclusive)'
          });
        }
        
        const response = await axios.get(`/api/transactions/filtered?${params}`);
        
        // Handle empty results
        if (response.data.transactions.length === 0) {
          if (startDateFilter || endDateFilter) {
            setError("指定された期間にトランザクションがありません。");
          } else {
            setError("");
          }
        } else {
          setError("");
        }
        
        setTransactions(response.data.transactions);
        setTotalItems(response.data.total);
      } catch (err: any) {
        console.error("Failed to load transactions:", err);
        if (err.code === 'ERR_NETWORK' || err.response?.status === 404) {
          setError("Backend server is not running. Please start the backend server on port 8000. Run './run_dev.sh' (Unix/Mac) or 'run_dev.bat' (Windows) from the project root.");
        } else {
          setError("トランザクションの読み込みに失敗しました。もう一度お試しください。");
        }
      } finally {
        setIsFilterLoading(false);
      }
    }, 500),
    [dateValidationError, startDateFilter, endDateFilter, typeFilter, currencyFilter, currentPage, itemsPerPage]
  );

  // Load transactions whenever filters or pagination changes
  useEffect(() => {
    debouncedLoadTransactions();
    return () => {
      debouncedLoadTransactions.cancel();
    };
  }, [currentPage, itemsPerPage, typeFilter, currencyFilter, startDateFilter, endDateFilter, forceReload, debouncedLoadTransactions]);

  // Load available currencies on component mount
  useEffect(() => {
    const loadCurrencies = async () => {
      try {
        const response = await axios.get("/api/currencies");
        setAvailableCurrencies(response.data);
      } catch (err: any) {
        console.error("Failed to load currencies:", err);
      }
    };
    loadCurrencies();
  }, []);

  const addTransaction = async () => {
    if (!date || !currency || !amount || !price) {
      setError("Please fill all required fields");
      return;
    }
    
    // Prevent duplicate submissions
    if (isSubmitting) {
      return;
    }
    
    setIsSubmitting(true);

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
      
      // Reset to page 1 to see the new transaction
      setCurrentPage(1);
      
      // Reload currencies if this is a new currency
      if (!availableCurrencies.includes(currency.toUpperCase())) {
        const response = await axios.get("/api/currencies");
        setAvailableCurrencies(response.data);
      }
      
      // Reset form
      setDate("");
      setCurrency("");
      setAmount("");
      setPrice("");
      setFee("0");
      setTotalValue("0.00");
      setError("");
    } catch (err: any) {
      if (err.code === 'ERR_NETWORK' || err.response?.status === 404) {
        setError("Backend server is not running. Please start the backend server on port 8000.");
      } else {
        setError(err.response?.data?.detail || "Failed to save transaction");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const removeTransaction = async (index: number) => {
    const transaction = transactions[index];
    
    try {
      // If transaction has an ID, delete from database
      if (transaction.id) {
        await axios.delete(`/api/transactions/${transaction.id}`);
        
        // If we're deleting the last item on a page (except page 1), go to previous page
        if (transactions.length === 1 && currentPage > 1) {
          setCurrentPage(currentPage - 1);
        } else {
          // Trigger reload by incrementing forceReload
          setForceReload(prev => prev + 1);
        }
        
        // Reload currencies list
        const response = await axios.get("/api/currencies");
        setAvailableCurrencies(response.data);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to delete transaction");
    }
  };

  const startEditTransaction = (transaction: Transaction) => {
    setEditingTransaction(transaction);
    setEditDate(transaction.date);
    setEditType(transaction.type);
    setEditCurrency(transaction.currency);
    setEditAmount(transaction.amount.toString());
    setEditPrice(transaction.price.toString());
    setEditFee(transaction.fee.toString());
  };

  const cancelEdit = () => {
    setEditingTransaction(null);
    setEditDate("");
    setEditType("buy");
    setEditCurrency("");
    setEditAmount("");
    setEditPrice("");
    setEditFee("0");
  };

  const saveEditTransaction = async () => {
    if (!editingTransaction || !editingTransaction.id) return;
    
    if (!editDate || !editCurrency || !editAmount || !editPrice) {
      setError("Please fill all required fields");
      return;
    }

    const updatedTransaction: Transaction = {
      ...editingTransaction,
      date: editDate,
      type: editType,
      currency: editCurrency.toUpperCase(),
      amount: parseFloat(editAmount),
      price: parseFloat(editPrice),
      fee: parseFloat(editFee) || 0,
    };

    try {
      // Update in database
      const response = await axios.put(`/api/transactions/${editingTransaction.id}`, updatedTransaction);
      const savedTransaction = response.data;
      
      // Trigger reload to reflect changes
      setForceReload(prev => prev + 1);
      
      // Reload currencies if this is a new currency
      if (!availableCurrencies.includes(editCurrency.toUpperCase())) {
        const response = await axios.get("/api/currencies");
        setAvailableCurrencies(response.data);
      }
      
      // Clear edit state
      cancelEdit();
      setError("");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to update transaction");
    }
  };

  const removeDuplicates = async () => {
    setLoading(true);
    try {
      const response = await axios.post("/api/transactions/remove-duplicates");
      if (response.data.duplicates_removed > 0) {
        setError("");
        alert(`Successfully removed ${response.data.duplicates_removed} duplicate transactions`);
        // Force reload transactions by triggering the useEffect
        const offset = (currentPage - 1) * itemsPerPage;
        const params = new URLSearchParams({
          limit: itemsPerPage.toString(),
          offset: offset.toString()
        });
        
        if (typeFilter !== "both") {
          params.append("type", typeFilter);
        }
        
        if (currencyFilter) {
          params.append("currency", currencyFilter);
        }
        
        if (startDateFilter) {
          params.append("start_date", startDateFilter);
        }
        
        if (endDateFilter) {
          params.append("end_date", endDateFilter);
        }
        
        const reloadResponse = await axios.get(`/api/transactions/filtered?${params}`);
        setTransactions(reloadResponse.data.transactions);
        setTotalItems(reloadResponse.data.total);
      } else {
        alert("No duplicate transactions found");
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to remove duplicates");
    } finally {
      setLoading(false);
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
              const updateResponse = await axios.put(`/api/transactions/${tx.id}`, updatedTx);
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
          <div className="grid grid-cols-7 gap-6">
            <div className="col-span-7 sm:col-span-1">
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

            <div className="col-span-7 sm:col-span-1">
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

            <div className="col-span-7 sm:col-span-1">
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

            <div className="col-span-7 sm:col-span-1">
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

            <div className="col-span-7 sm:col-span-1">
              <label className="block text-sm font-medium text-gray-700">
                Unit Price (USD)
              </label>
              <input
                type="number"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                step="0.01"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              />
            </div>

            <div className="col-span-7 sm:col-span-1">
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

            <div className="col-span-7 sm:col-span-1">
              <label className="block text-sm font-medium text-gray-700">
                Total Value (USD)
              </label>
              <input
                type="text"
                value={`$${totalValue}`}
                disabled
                className="mt-1 block w-full rounded-md border-gray-300 bg-gray-100 shadow-sm sm:text-sm"
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
              disabled={isSubmitting}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? "Adding..." : "Add Transaction"}
            </button>
          </div>
        </div>
      </div>

      {/* Transactions Table */}
      {totalItems > 0 && (
        <div className="mt-8 bg-white shadow sm:rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium leading-6 text-gray-900">
                Transactions
                {(typeFilter !== "both" || currencyFilter || startDateFilter || endDateFilter) && (
                  <span className="ml-2 text-sm font-normal text-gray-500">
                    (filtered)
                  </span>
                )}
              </h3>
              
              {/* Filter Controls */}
              <div className="flex gap-4 items-center">
                {/* Items per page */}
                <div className="flex items-center gap-2">
                  <label className="text-sm text-gray-700">Items per page:</label>
                  <select
                    value={itemsPerPage}
                    onChange={(e) => {
                      setItemsPerPage(Number(e.target.value));
                      setCurrentPage(1);
                    }}
                    className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  >
                    <option value={10}>10</option>
                    <option value={50}>50</option>
                    <option value={100}>100</option>
                  </select>
                </div>
                
                {/* Type filter */}
                <div className="flex items-center gap-2">
                  <label className="text-sm text-gray-700">Type:</label>
                  <select
                    value={typeFilter}
                    onChange={(e) => {
                      setTypeFilter(e.target.value as "buy" | "sell" | "both");
                      setCurrentPage(1);
                    }}
                    className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  >
                    <option value="both">Both</option>
                    <option value="buy">Buy</option>
                    <option value="sell">Sell</option>
                  </select>
                </div>
                
                {/* Currency filter */}
                <div className="flex items-center gap-2">
                  <label className="text-sm text-gray-700">Currency:</label>
                  <select
                    value={currencyFilter}
                    onChange={(e) => {
                      setCurrencyFilter(e.target.value);
                      setCurrentPage(1);
                    }}
                    className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  >
                    <option value="">All</option>
                    {availableCurrencies.map((currency) => (
                      <option key={currency} value={currency}>
                        {currency}
                      </option>
                    ))}
                  </select>
                </div>
                
                {/* Date range filters */}
                <DateFilterErrorBoundary>
                  <div className="flex items-center gap-2">
                    <label htmlFor="start-date" className="text-sm text-gray-700">開始日:</label>
                    <input
                      id="start-date"
                      type="date"
                      value={startDateFilter}
                      placeholder="YYYY-MM-DD"
                      aria-describedby="start-date-help"
                      onChange={(e) => {
                        console.log('[Frontend Debug] Start date changed:', e.target.value);
                        setStartDateFilter(e.target.value);
                        setCurrentPage(1);
                      }}
                      className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                      min="2020-01-01"
                      max={new Date().toISOString().split('T')[0]}
                    />
                    <span id="start-date-help" className="sr-only">
                      YYYY-MM-DD形式で日付を入力してください
                    </span>
                    {startDateFilter && (
                      <span className="text-xs text-gray-500">選択: {startDateFilter}</span>
                    )}
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <label htmlFor="end-date" className="text-sm text-gray-700">終了日:</label>
                    <input
                      id="end-date"
                      type="date"
                      value={endDateFilter}
                      placeholder="YYYY-MM-DD"
                      aria-describedby="end-date-help"
                      onChange={(e) => {
                        console.log('[Frontend Debug] End date changed:', e.target.value);
                        setEndDateFilter(e.target.value);
                        setCurrentPage(1);
                      }}
                      className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                      min="2020-01-01"
                      max={new Date().toISOString().split('T')[0]}
                    />
                    <span id="end-date-help" className="sr-only">
                      YYYY-MM-DD形式で日付を入力してください
                    </span>
                    {endDateFilter && (
                      <span className="text-xs text-gray-500">選択: {endDateFilter}</span>
                    )}
                  </div>
                </DateFilterErrorBoundary>
                
                {/* Clear filters button */}
                {(typeFilter !== "both" || currencyFilter || startDateFilter || endDateFilter) && (
                  <button
                    onClick={() => {
                      setTypeFilter("both");
                      setCurrencyFilter("");
                      setStartDateFilter("");
                      setEndDateFilter("");
                      setCurrentPage(1);
                    }}
                    className="ml-2 text-sm text-gray-500 hover:text-gray-700 underline"
                  >
                    Clear filters
                  </button>
                )}
              </div>
            </div>
            
            {/* Filtering state display */}
            {(startDateFilter || endDateFilter) && (
              <div className="bg-blue-50 border border-blue-200 rounded-md p-3 mb-4 flex justify-between items-center">
                <p className="text-sm text-blue-800">
                  フィルタリング中: {startDateFilter || '全期間'} から {endDateFilter || '現在'} まで
                  （{totalItems}件中）
                </p>
                <button
                  onClick={() => {
                    setStartDateFilter('');
                    setEndDateFilter('');
                    setCurrentPage(1);
                  }}
                  className="text-sm text-blue-600 hover:text-blue-800 underline focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                  aria-label="日付フィルタをクリア"
                >
                  フィルタをクリア
                </button>
              </div>
            )}
            
            {/* Date validation error */}
            {dateValidationError && (
              <div className="text-red-600 text-sm mt-1 mb-4" role="alert">{dateValidationError}</div>
            )}
            
            {/* Loading state for filtering */}
            {isFilterLoading && (startDateFilter || endDateFilter) && (
              <div className="flex justify-center items-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-500"></div>
                <span className="ml-2 text-gray-500">日付範囲でフィルタリング中...</span>
              </div>
            )}
            
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
                      Unit Price
                    </th>
                    <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                      Total Value
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
                  {transactions.map((tx) => (
                    <tr key={tx.id || `${tx.date}-${tx.type}-${tx.currency}-${tx.amount}`}>
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
                        ${(tx.amount * tx.price).toFixed(2)}
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
                          onClick={() => startEditTransaction(tx)}
                          className="text-indigo-600 hover:text-indigo-900 mr-3"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => removeTransaction(transactions.findIndex(t => t === tx))}
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

            {/* Pagination Controls */}
            {totalItems > itemsPerPage && (
              <div className="mt-4 flex items-center justify-between">
                <div className="text-sm text-gray-700">
                  Showing {(currentPage - 1) * itemsPerPage + 1} to {Math.min(currentPage * itemsPerPage, totalItems)} of {totalItems} results
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setCurrentPage(currentPage - 1)}
                    disabled={currentPage === 1}
                    className="px-3 py-1 text-sm font-medium rounded-md bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  
                  {/* Page Numbers */}
                  {(() => {
                    const totalPages = Math.ceil(totalItems / itemsPerPage);
                    const pageNumbers = [];
                    const maxPagesToShow = 5;
                    
                    let startPage = Math.max(1, currentPage - Math.floor(maxPagesToShow / 2));
                    let endPage = Math.min(totalPages, startPage + maxPagesToShow - 1);
                    
                    if (endPage - startPage + 1 < maxPagesToShow) {
                      startPage = Math.max(1, endPage - maxPagesToShow + 1);
                    }
                    
                    for (let i = startPage; i <= endPage; i++) {
                      pageNumbers.push(
                        <button
                          key={i}
                          onClick={() => setCurrentPage(i)}
                          className={`px-3 py-1 text-sm font-medium rounded-md ${
                            i === currentPage
                              ? "bg-indigo-600 text-white"
                              : "bg-white border border-gray-300 text-gray-700 hover:bg-gray-50"
                          }`}
                        >
                          {i}
                        </button>
                      );
                    }
                    
                    return pageNumbers;
                  })()}
                  
                  <button
                    onClick={() => setCurrentPage(currentPage + 1)}
                    disabled={currentPage === Math.ceil(totalItems / itemsPerPage)}
                    className="px-3 py-1 text-sm font-medium rounded-md bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}

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

              <div className="flex gap-2">
                <button
                  onClick={removeDuplicates}
                  disabled={loading}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? "Removing..." : "Remove Duplicates"}
                </button>
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
        </div>
      )}

      {/* Empty State */}
      {totalItems === 0 && !loading && (
        <div className="mt-8 bg-white shadow sm:rounded-lg">
          <div className="px-4 py-5 sm:p-6 text-center">
            <p className="text-gray-500">No transactions found. Add your first transaction above to get started.</p>
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

      {/* Edit Transaction Modal */}
      {editingTransaction && (
        <div className="fixed z-10 inset-0 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true" onClick={cancelEdit}></div>
            
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                  Edit Transaction
                </h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Date</label>
                    <input
                      type="date"
                      value={editDate}
                      onChange={(e) => setEditDate(e.target.value)}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Type</label>
                    <select
                      value={editType}
                      onChange={(e) => setEditType(e.target.value as "buy" | "sell")}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    >
                      <option value="buy">Buy</option>
                      <option value="sell">Sell</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Currency</label>
                    <input
                      type="text"
                      value={editCurrency}
                      onChange={(e) => setEditCurrency(e.target.value)}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Amount</label>
                    <input
                      type="number"
                      value={editAmount}
                      onChange={(e) => setEditAmount(e.target.value)}
                      step="0.00000001"
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Unit Price (USD)</label>
                    <input
                      type="number"
                      value={editPrice}
                      onChange={(e) => setEditPrice(e.target.value)}
                      step="0.01"
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Fee (USD)</label>
                    <input
                      type="number"
                      value={editFee}
                      onChange={(e) => setEditFee(e.target.value)}
                      step="0.01"
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Total Value (USD)</label>
                    <input
                      type="text"
                      value={`$${((parseFloat(editAmount) || 0) * (parseFloat(editPrice) || 0)).toFixed(2)}`}
                      disabled
                      className="mt-1 block w-full rounded-md border-gray-300 bg-gray-100 shadow-sm sm:text-sm"
                    />
                  </div>
                </div>
                
                {error && (
                  <div className="mt-4 rounded-md bg-red-50 p-4">
                    <div className="text-sm text-red-800">{error}</div>
                  </div>
                )}
              </div>
              
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  onClick={saveEditTransaction}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Save
                </button>
                <button
                  type="button"
                  onClick={cancelEdit}
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Debug Mode Panel */}
      {process.env.NODE_ENV === 'development' && (
        <div className="mt-4 bg-gray-100 p-4 rounded-lg">
          <details>
            <summary className="cursor-pointer font-semibold text-gray-700">
              🔍 デバッグ情報
            </summary>
            <div className="mt-2 space-y-2">
              <pre className="bg-white p-3 rounded text-xs overflow-x-auto">
{JSON.stringify({
  filters: {
    startDate: startDateFilter,
    endDate: endDateFilter,
  },
  results: {
    totalItems,
    currentPage,
    totalPages: Math.ceil(totalItems / itemsPerPage),
  },
  api: {
    endpoint: '/api/transactions/filtered',
    params: new URLSearchParams({
      start_date: startDateFilter,
      end_date: endDateFilter,
      page: currentPage.toString(),
      page_size: itemsPerPage.toString(),
    }).toString(),
  },
  validation: {
    dateError: dateValidationError,
    isLoading: isFilterLoading,
  }
}, null, 2)}
              </pre>
              <a 
                href="/dashboard/debug" 
                className="inline-block text-sm text-blue-600 hover:underline"
              >
                詳細なデバッグツールへ →
              </a>
            </div>
          </details>
        </div>
      )}
    </div>
  );
}