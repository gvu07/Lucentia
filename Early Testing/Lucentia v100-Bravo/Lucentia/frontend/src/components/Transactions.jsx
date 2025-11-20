import React, { useState, useEffect } from 'react';
import { dashboardAPI } from '../api';
import { 
  CurrencyDollarIcon, 
  CalendarIcon, 
  TagIcon,
  BuildingStorefrontIcon
} from '@heroicons/react/24/outline';

const Transactions = () => {
  const [transactions, setTransactions] = useState([]);
  const [totalTransactions, setTotalTransactions] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [dateRange, setDateRange] = useState('30');

  useEffect(() => {
    let isCancelled = false;

    const fetchTransactions = async () => {
      setLoading(true);
      try {
        const limit = 50;
        const offset = (page - 1) * limit;
        const { startDate, endDate } = getDateRangeBounds();
        const data = await dashboardAPI.getTransactions(limit, offset, startDate, endDate);

        if (isCancelled) return;

        setTotalTransactions(data.total || 0);
        setHasMore(((data.items?.length || 0) + offset) < (data.total || 0));
        setTransactions((prev) =>
          page === 1 ? data.items || [] : [...prev, ...(data.items || [])]
        );
      } catch (error) {
        if (!isCancelled) {
          setError('Failed to load transactions');
        }
      } finally {
        if (!isCancelled) {
          setLoading(false);
        }
      }
    };

    fetchTransactions();

    return () => {
      isCancelled = true;
    };
  }, [page, dateRange]);

  const getDateRangeBounds = () => {
    const days = parseInt(dateRange, 10);
    const end = new Date();
    const start = new Date();
    start.setDate(end.getDate() - (isNaN(days) ? 30 : days) + 1);
    return {
      startDate: start.toISOString().split('T')[0],
      endDate: end.toISOString().split('T')[0],
    };
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const getCategoryColor = (category) => {
    if (!category) return 'bg-gray-100 text-gray-800';
    const normalized = category.replace(/_/g, ' ').toLowerCase();
    const colors = {
      'food and drink': 'bg-orange-100 text-orange-800',
      'transportation': 'bg-blue-100 text-blue-800',
      'general merchandise': 'bg-purple-100 text-purple-800',
      'entertainment': 'bg-pink-100 text-pink-800',
      'healthcare': 'bg-green-100 text-green-800',
      'travel': 'bg-indigo-100 text-indigo-800',
      'income': 'bg-emerald-100 text-emerald-800',
    };
    return colors[normalized] || 'bg-gray-100 text-gray-800';
  };

  const formatCategoryLabel = (category) => {
    if (!category) return '';
    return category
      .toLowerCase()
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const loadMore = () => {
    if (hasMore && !loading) {
      setPage(prev => prev + 1);
    }
  };

  const handleDateRangeChange = (event) => {
    setTransactions([]);
    setTotalTransactions(0);
    setPage(1);
    setHasMore(true);
    setDateRange(event.target.value);
  };

  if (loading && transactions.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center text-red-600">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-[#F8F9FF] rounded-lg border border-transparent p-6">
        <h1 className="text-3xl font-bold text-gray-900">Transactions</h1>
        <p className="mt-2 text-gray-600">
          View and analyze your recent financial transactions.
        </p>
        <div className="mt-4">
          <span className="text-sm text-gray-500">
            Total transactions: <span className="font-medium text-primary-600">{totalTransactions}</span>
          </span>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-[#F8F9FF] rounded-lg border border-transparent p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label htmlFor="search" className="block text-sm font-medium text-gray-700">
              Search Transactions
            </label>
            <input
              type="text"
              id="search"
              className="mt-1 input-field"
              placeholder="Search by merchant or description..."
            />
          </div>
          
          <div>
            <label htmlFor="category" className="block text-sm font-medium text-gray-700">
              Category
            </label>
            <select
              id="category"
              className="mt-1 input-field"
            >
              <option value="">All Categories</option>
              <option value="Food and Drink">Food and Drink</option>
              <option value="Transportation">Transportation</option>
              <option value="Shopping">Shopping</option>
              <option value="Entertainment">Entertainment</option>
              <option value="Health">Health</option>
              <option value="Travel">Travel</option>
            </select>
          </div>
          
          <div>
            <label htmlFor="dateRange" className="block text-sm font-medium text-gray-700">
              Date Range
            </label>
            <select
              id="dateRange"
              className="mt-1 input-field"
              value={dateRange}
              onChange={handleDateRangeChange}
            >
              <option value="7">Last 7 days</option>
              <option value="30">Last 30 days</option>
              <option value="90">Last 90 days</option>
              <option value="365">Last year</option>
            </select>
          </div>
        </div>
      </div>

      {/* Transactions List */}
      <div className="rounded-lg border border-[#C7CBE4] shadow-sm bg-gradient-to-br from-[#EEF0FF] via-[#F8F9FF] to-white">
        <div className="space-y-3 p-4">
          {transactions.map((transaction) => (
            <div
              key={transaction.id}
              className="rounded-2xl border border-white/60 bg-white/80 backdrop-blur-sm shadow-sm hover:shadow-md transition"
            >
              <div className="flex flex-wrap gap-4 items-center p-4">
                <div className="flex items-center gap-3 flex-1 min-w-[200px]">
                  <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-indigo-100 to-white flex items-center justify-center text-indigo-600 font-semibold">
                    {transaction.merchant_name?.[0] || transaction.name?.[0] || '?'}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-[#1F2330]">
                      {transaction.merchant_name || transaction.name}
                    </p>
                    <p className="text-xs text-[#6F7385] capitalize">
                      {transaction.payment_channel || 'card'}
                    </p>
                  </div>
                </div>
                <div className="flex items-center">
                  <span
                    className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${getCategoryColor(
                      transaction.category_primary
                    )}`}
                  >
                    {formatCategoryLabel(transaction.category_primary) || 'Uncategorized'}
                  </span>
                </div>
                <div className="text-sm font-semibold text-[#1F2330] min-w-[120px] text-right">
                  {formatCurrency(transaction.amount)}
                </div>
                <div className="text-xs text-[#6F7385] min-w-[120px] text-right">
                  {new Date(transaction.date).toLocaleDateString()}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Load More */}
        {hasMore && (
          <div className="px-6 py-4 bg-gradient-to-r from-[#EEF0FF] to-[#F8F9FF] border-t border-white/60">
            <button
              onClick={loadMore}
              disabled={loading}
              className="btn-primary w-full flex justify-center py-2 px-4"
            >
              {loading ? 'Loading...' : 'Load More Transactions'}
            </button>
          </div>
        )}
      </div>

      {transactions.length === 0 && (
        <div className="text-center py-12">
          <CurrencyDollarIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No transactions found</h3>
          <p className="mt-1 text-sm text-gray-500">
            Transactions will appear here after you connect your bank account.
          </p>
        </div>
      )}
    </div>
  );
};

export default Transactions;
