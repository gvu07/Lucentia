import React, { useState, useEffect } from 'react';
import { dashboardAPI } from '../api';
import { 
  CreditCardIcon, 
  BanknotesIcon, 
  BuildingLibraryIcon,
  PlusIcon
} from '@heroicons/react/24/outline';

const Accounts = () => {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAccounts();
  }, []);

  const fetchAccounts = async () => {
    try {
      const data = await dashboardAPI.getAccounts();
      setAccounts(data);
    } catch (error) {
      setError('Failed to load accounts');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount || 0);
  };

  const getAccountIcon = (type) => {
    switch (type) {
      case 'credit':
        return CreditCardIcon;
      case 'depository':
        return BanknotesIcon;
      case 'loan':
        return BuildingLibraryIcon;
      default:
        return CreditCardIcon;
    }
  };

  const getAccountColor = (type) => {
    switch (type) {
      case 'credit':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'depository':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'loan':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const totalBalance = accounts.reduce((sum, account) => sum + (account.current_balance || 0), 0);
  const totalAvailable = accounts.reduce((sum, account) => sum + (account.available_balance || 0), 0);

  if (loading) {
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
        <h1 className="text-3xl font-bold text-gray-900">Connected Accounts</h1>
        <p className="mt-2 text-gray-600">
          Manage your linked bank accounts and view their balances.
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <BanknotesIcon className="h-8 w-8 text-green-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Total Balance</dt>
                <dd className="text-2xl font-bold text-gray-900">
                  {formatCurrency(totalBalance)}
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CreditCardIcon className="h-8 w-8 text-blue-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Total Available</dt>
                <dd className="text-2xl font-bold text-gray-900">
                  {formatCurrency(totalAvailable)}
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      {/* Accounts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {accounts.map((account) => {
          const AccountIcon = getAccountIcon(account.type);
          const statusColor = account.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800';
          
          return (
            <div key={account.id} className="card hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <div className={`p-2 rounded-lg ${getAccountColor(account.type)}`}>
                    <AccountIcon className="h-6 w-6" />
                  </div>
                  <div className="ml-3">
                    <h3 className="text-lg font-medium text-gray-900">
                      {account.name}
                    </h3>
                    <p className="text-sm text-gray-500">
                      {account.official_name || account.subtype || account.type}
                    </p>
                  </div>
                </div>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColor}`}>
                  {account.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Current Balance:</span>
                  <span className="text-sm font-medium text-gray-900">
                    {formatCurrency(account.current_balance)}
                  </span>
                </div>
                
                {account.available_balance !== null && account.available_balance !== account.current_balance && (
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">Available Balance:</span>
                    <span className="text-sm font-medium text-gray-900">
                      {formatCurrency(account.available_balance)}
                    </span>
                  </div>
                )}
                
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Account Type:</span>
                  <span className="text-sm font-medium text-gray-900 capitalize">
                    {account.type}
                  </span>
                </div>
                
                {account.currency_code && (
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">Currency:</span>
                    <span className="text-sm font-medium text-gray-900">
                      {account.currency_code}
                    </span>
                  </div>
                )}
              </div>

              <div className="mt-6 pt-4 border-t border-gray-200">
                <div className="text-xs text-gray-500">
                  Last updated: {new Date(account.updated_at).toLocaleDateString()}
                </div>
              </div>
            </div>
          );
        })}

        {/* Add Account Card */}
        <div className="card border-2 border-dashed border-gray-300 hover:border-primary-400 transition-colors cursor-pointer">
          <div className="flex flex-col items-center justify-center h-full py-8">
            <PlusIcon className="h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Add New Account</h3>
            <p className="text-sm text-gray-500 text-center">
              Connect another bank account to get more insights
            </p>
          </div>
        </div>
      </div>

      {accounts.length === 0 && (
        <div className="text-center py-12">
          <BuildingLibraryIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No accounts connected</h3>
          <p className="mt-1 text-sm text-gray-500">
            Connect your bank account to start tracking your finances and getting insights.
          </p>
        </div>
      )}
    </div>
  );
};

export default Accounts;
