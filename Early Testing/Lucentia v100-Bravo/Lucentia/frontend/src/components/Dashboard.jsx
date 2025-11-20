import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { dashboardAPI } from '../api';
import {
  BanknotesIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ChartPieIcon,
  CurrencyDollarIcon
} from '@heroicons/react/24/outline';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  ComposedChart,
  Area,
  Line,
} from 'recharts';

const PRIORITY_RANK = { high: 0, medium: 1, low: 2 };
// Higher quickScale = more immediately actionable for Quick Insights
const QUICK_SCALE = {
  restaurant_comeback: 5,
  favorite_restaurant_push: 5,
  payment_method_optimization: 5,
  category_subscription_opportunity: 5,
  cross_user_affinity: 4,
  merchant_loyalty: 4,
  merchant_bundling: 4,
  duplicate_services: 4,
  duplicate_subscription: 4,
  category_spike: 4,
  category_trend: 3,
  fee_detection: 3,
  balance_warning: 5,
  cash_buffer: 5,
  air_travel_footprint: 3,
  default: 2,
};

const getPriorityRank = (value) => {
  if (!value) return 3;
  const normalized = String(value).toLowerCase();
  return PRIORITY_RANK[normalized] ?? 3;
};

const parseTimestamp = (value) => {
  if (!value) return 0;
  const time = Date.parse(value);
  return Number.isNaN(time) ? 0 : time;
};

const scoreInsight = (insight) => {
  const priorityScore = getPriorityRank(insight?.priority);
  const recencyScore = -parseTimestamp(insight?.created_at || insight?.updated_at);
  const family = insight?.familyKey || insight?.family;
  const quickScore = QUICK_SCALE[family] ?? QUICK_SCALE.default;
  return { priorityScore, quickScore, recencyScore };
};

const compareInsights = (a, b) => {
  const aScore = scoreInsight(a);
  const bScore = scoreInsight(b);
  if (aScore.quickScore !== bScore.quickScore) {
    return bScore.quickScore - aScore.quickScore;
  }
  if (aScore.priorityScore !== bScore.priorityScore) {
    return aScore.priorityScore - bScore.priorityScore;
  }
  return aScore.recencyScore - bScore.recencyScore;
};

const getDiverseInsights = (insights, limit = 6) => {
  if (!Array.isArray(insights) || !insights.length) {
    return [];
  }

  const buckets = Object.values(
    insights.reduce((acc, insight) => {
      const familyKey = insight.family || insight.familyKey || 'uncategorized';
      if (!acc[familyKey]) {
        acc[familyKey] = { familyKey, insights: [] };
      }
      acc[familyKey].insights.push(insight);
      return acc;
    }, {})
  );

  buckets.forEach((bucket) => bucket.insights.sort(compareInsights));

  const sortBuckets = () =>
    buckets.sort((a, b) => {
      if (!a.insights.length && !b.insights.length) return 0;
      if (!a.insights.length) return 1;
      if (!b.insights.length) return -1;
      return compareInsights(a.insights[0], b.insights[0]);
    });

  sortBuckets();

  const selection = [];
  while (selection.length < limit) {
    let addedInPass = false;
    for (const bucket of buckets) {
      if (!bucket.insights.length) {
        continue;
      }
      selection.push(bucket.insights.shift());
      addedInPass = true;
      if (selection.length === limit) {
        break;
      }
    }
    if (!addedInPass) {
      break;
    }
    sortBuckets();
  }

  return selection;
};

const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const RADIAN = Math.PI / 180;

const truncateLabel = (value, maxLength = 18) => {
  if (!value) return '';
  if (value.length <= maxLength) {
    return value;
  }
  return `${value.slice(0, Math.max(0, maxLength - 3))}...`;
};

const formatPercentLabel = (value) => {
  if (!value) {
    return '0%';
  }
  const percentage = value * 100;
  if (percentage > 0 && percentage < 1) {
    return '<1%';
  }
  return `${Math.round(percentage)}%`;
};

const toPolarPoint = (cx, cy, radius, angle) => ({
  x: cx + radius * Math.cos(angle),
  y: cy + radius * Math.sin(angle),
});

const getConnectorPoints = ({ cx, cy, midAngle, outerRadius }) => {
  const angle = -midAngle * RADIAN;
  const start = toPolarPoint(cx, cy, outerRadius + 6, angle);
  const control = toPolarPoint(cx, cy, outerRadius + 26, angle);
  const end = toPolarPoint(cx, cy, outerRadius + 70, angle);
  return { start, control, end, isRightSide: end.x >= cx };
};

const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

const renderCategoryLabel = ({ cx, cy, midAngle, outerRadius, percent, name, viewBox }) => {
  if (!name) {
    return null;
  }

  const safePercent = Number.isFinite(percent) ? percent : 0;
  const radius = Number(outerRadius) || 0;
  const { start, control, end, isRightSide } = getConnectorPoints({
    cx,
    cy,
    midAngle,
    outerRadius: radius,
  });
  const chartWidth = viewBox?.width || cx * 2 || 0;
  const chartHeight = viewBox?.height || cy * 2 || 0;
  const canvasPadding = 16;
  const textX = end.x + (isRightSide ? 12 : -12);
  const label = `${truncateLabel(name, 24)} - ${formatPercentLabel(safePercent)}`;
  const approxTextWidth = Math.min(label.length, 32) * 7;

  const clampedEndX = clamp(end.x, canvasPadding + 8, chartWidth - canvasPadding - 8);
  const clampedEndY = clamp(end.y, canvasPadding, chartHeight - canvasPadding);

  const targetTextX = isRightSide
    ? Math.min(textX, chartWidth - canvasPadding - approxTextWidth)
    : Math.max(textX, canvasPadding + approxTextWidth);
  const textY = clampedEndY;

  return (
    <g>
      <path
        d={`M${start.x},${start.y} Q${control.x},${control.y} ${clampedEndX},${clampedEndY}`}
        fill="none"
        stroke="rgba(79, 70, 229, 0.45)"
        strokeWidth={1.5}
        strokeLinecap="round"
      />
      <circle cx={clampedEndX} cy={clampedEndY} r={2.4} fill="rgba(79, 70, 229, 0.65)" />
      <text
        x={targetTextX}
        y={textY}
        fill="#0F172A"
        textAnchor={isRightSide ? 'start' : 'end'}
        dominantBaseline="middle"
        style={{
          fontSize: '0.8rem',
          fontWeight: 600,
          pointerEvents: 'none',
          paintOrder: 'stroke',
          stroke: 'rgba(255,255,255,0.95)',
          strokeWidth: 4,
        }}
      >
        {label}
      </text>
    </g>
  );
};

const toMonthKey = (date) => `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, '0')}`;
const monthKeyToDate = (key) => {
  const [year, month] = key.split('-').map((value) => Number(value));
  return new Date(Date.UTC(year, month - 1, 1));
};

const getMonthLabel = (date, projected = false) => {
  const base = MONTH_NAMES[date.getUTCMonth()];
  return projected ? `${base} (Projected)` : base;
};

const average = (values) => {
  if (!values.length) return 0;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
};

const stddev = (values) => {
  if (values.length < 2) return 0;
  const avg = average(values);
  const variance = average(values.map((value) => (value - avg) ** 2));
  return Math.sqrt(variance);
};

const formatCategoryLabel = (label) => {
  if (!label) return 'General';
  return label
    .toLowerCase()
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

const formatProjectionValue = (value) => {
  const rounded = Math.round(Math.abs(value));
  return `$${rounded.toLocaleString()}`;
};

const buildFinancialProjection = (transactions, currentBalance) => {
  if (!Array.isArray(transactions) || !transactions.length || currentBalance === null || currentBalance === undefined) {
    return { hasData: false, reason: 'collecting' };
  }

  const monthBuckets = new Map();
  transactions.forEach((transaction) => {
    const date = new Date(transaction.date);
    if (Number.isNaN(date.getTime())) return;
    const key = toMonthKey(date);
    if (!monthBuckets.has(key)) {
      monthBuckets.set(key, {
        income: 0,
        spending: 0,
        categories: {},
        incomeEvents: [],
        spendingEvents: [],
        sampleTransactions: [],
      });
    }
    const bucket = monthBuckets.get(key);
    const amount = Number(transaction.amount) || 0;
    const category = formatCategoryLabel(transaction.category_primary || 'Other');
    bucket.sampleTransactions.push(transaction);

    if (amount < 0) {
      const incomeAmount = Math.abs(amount);
      bucket.income += incomeAmount;
      bucket.incomeEvents.push(incomeAmount);
    } else {
      bucket.spending += amount;
      bucket.spendingEvents.push(amount);
      bucket.categories[category] = (bucket.categories[category] || 0) + amount;
    }
  });

  const orderedKeys = Array.from(monthBuckets.keys()).sort();
  const MAX_HISTORY = 6;
  const selectedKeys = orderedKeys.slice(-MAX_HISTORY);
  const monthlyData = selectedKeys.map((key) => {
    const bucket = monthBuckets.get(key);
    const date = monthKeyToDate(key);
    const total = bucket.spending || 1;
    const topCategories = Object.entries(bucket.categories)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 2)
      .map(([name, value]) => `${name}: ${Math.round((value / total) * 100)}%`);
    return {
      key,
      date,
      label: getMonthLabel(date),
      income: bucket.income,
      spending: bucket.spending,
      net: bucket.income - bucket.spending,
      categories: bucket.categories,
      topCategories,
      incomeEvents: bucket.incomeEvents,
      spendingEvents: bucket.spendingEvents,
      sampleTransactions: bucket.sampleTransactions,
    };
  });

  if (monthlyData.length < 3) {
    return { hasData: false, reason: 'insufficient' };
  }

  const avgIncome = average(monthlyData.map((m) => m.income).filter((value) => value > 0));
  const avgSpending = average(monthlyData.map((m) => m.spending));
  const spendingStd = stddev(monthlyData.map((m) => m.spending));
  const netChange = avgIncome - avgSpending;
  const volatility = spendingStd || avgSpending * 0.15;

  const incomeStd = stddev(monthlyData.flatMap((m) => m.incomeEvents));
  let incomeConfidence = 'low';
  if (avgIncome > 0) {
    const varianceRatio = incomeStd / avgIncome;
    if (varianceRatio < 0.2) {
      incomeConfidence = 'high';
    } else if (varianceRatio < 0.45) {
      incomeConfidence = 'medium';
    }
  }

  const historical = [...monthlyData]
    .map((entry, index) => ({ ...entry, index }))
    .sort((a, b) => a.date - b.date);

  let runningBalance = Number(currentBalance) || 0;
  const reversed = [...historical].sort((a, b) => b.date - a.date);
  const historicalLine = [];
  reversed.forEach((entry) => {
    historicalLine.push({
      ...entry,
      balance: runningBalance,
    });
    runningBalance -= entry.net;
  });
  historicalLine.reverse();

  const lastHistoricalBalance =
    (historicalLine[historicalLine.length - 1]?.balance ?? Number(currentBalance)) || 0;
  const lastDate = historicalLine[historicalLine.length - 1]?.date || new Date();

  const FUTURE_MONTHS = 4;
  const projections = [];
  let projectedBalance = lastHistoricalBalance;
  let upperBalance = lastHistoricalBalance;
  let lowerBalance = lastHistoricalBalance;
  for (let i = 1; i <= FUTURE_MONTHS; i += 1) {
    const futureDate = new Date(Date.UTC(lastDate.getUTCFullYear(), lastDate.getUTCMonth() + i, 1));
    const projectedIncome = avgIncome;
    const projectedSpending = avgSpending;
    const projectedNet = netChange;
    projectedBalance += projectedNet;
    upperBalance += projectedNet + volatility;
    lowerBalance += projectedNet - volatility;
    projections.push({
      label: getMonthLabel(futureDate, true),
      date: futureDate,
      projectedIncome,
      projectedSpending,
      projectedNet,
      projectedBalance,
      upperBalance,
      lowerBalance,
    });
  }

  const timeline = [
    ...historicalLine.map((entry) => ({
      label: entry.label,
      date: entry.date,
      actualBalance: entry.balance,
      projectedBalance: null,
      lowerBound: entry.balance,
      upperBound: entry.balance,
      coneHeight: 0,
      isProjected: false,
      income: entry.income,
      spending: entry.spending,
      net: entry.net,
      topCategories: entry.topCategories,
      anomaly: spendingStd > 0 && entry.spending > avgSpending + spendingStd * 1.8,
    })),
    ...projections.map((entry) => ({
      label: entry.label,
      date: entry.date,
      actualBalance: null,
      projectedBalance: entry.projectedBalance,
      lowerBound: entry.lowerBalance,
      coneHeight: Math.max(entry.upperBalance - entry.lowerBalance, 0),
      isProjected: true,
      projectedIncome: entry.projectedIncome,
      projectedSpending: entry.projectedSpending,
      projectedNet: entry.projectedNet,
      incomeConfidence,
      upperBound: entry.upperBalance,
    })),
  ];

  const latestMonth = monthlyData[monthlyData.length - 1];
  const categoryEntries = Object.entries(latestMonth.categories || {})
    .sort((a, b) => b[1] - a[1])
    .slice(0, 2)
    .map(([name, value]) => ({
      label: name,
      percent: latestMonth.spending ? Math.round((value / latestMonth.spending) * 100) : 0,
      amount: value,
    }));

  const negativeMonths = monthlyData.filter((month) => month.net < 0).length;
  const riskIndicators = [];
  if (negativeMonths >= 2) {
    riskIndicators.push('Spending exceeded income in most recent months.');
  }
  if (projections.length && projections[projections.length - 1].lowerBalance < 0) {
    riskIndicators.push('Trajectory could dip below zero based on downside scenario.');
  }
  if (incomeConfidence === 'low') {
    riskIndicators.push('Income pattern is inconsistent — projection confidence is low.');
  }

  const netMagnitude = formatProjectionValue(netChange);
  const outlookSummary =
    netChange >= 0
      ? `You are projected to save ~${netMagnitude} per month if current habits hold.`
      : `At the current spending rate, your balance could fall by ~${netMagnitude} per month.`;

  const windowLabel = `${historicalLine.length} mo history · ${projections.length} mo forecast`;

  return {
    hasData: true,
    timeline,
    outlookSummary,
    riskIndicators,
    categoryImpacts: categoryEntries,
    incomeConfidence,
    expectedIncome: avgIncome,
    expectedSpending: avgSpending,
    projectedNet: netChange,
    windowLabel,
  };
};
const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [transactionsLoading, setTransactionsLoading] = useState(true);
  const [transactionsError, setTransactionsError] = useState(null);
  const [activeCategorySlice, setActiveCategorySlice] = useState(null);

  useEffect(() => {
    fetchDashboardData();
    fetchTransactions();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const data = await dashboardAPI.getDashboard();
      setDashboardData(data);
    } catch (error) {
      const detail = error.response?.data?.detail;
      setError(detail || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const fetchTransactions = async () => {
    try {
      setTransactionsError(null);
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - 90);
      const endDate = new Date();
      const response = await dashboardAPI.getTransactions(
        500,
        0,
        startDate.toISOString().split('T')[0],
        endDate.toISOString().split('T')[0]
      );
      const nowMs = Date.now();
      const items = (response?.items || [])
        .filter((item) => {
          const ts = new Date(item.date).getTime();
          return Number.isFinite(ts) && ts <= nowMs;
        })
        .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
      setTransactions(items);
    } catch (error) {
      setTransactionsError('Failed to load recent transactions');
    } finally {
      setTransactionsLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const categoryData = Object.entries(dashboardData?.top_categories || {}).map(([name, value]) => ({
    name: formatCategoryLabel(name),
    value: parseFloat(value),
  }));

  const allInsights =
    dashboardData?.insights?.domains?.flatMap((domain) =>
      domain.families.flatMap((family) =>
        family.insights.map((insight) => ({
          ...insight,
          domainKey: domain.key,
          familyKey: family.key,
        }))
      )
    ) || [];

  const quickInsights = getDiverseInsights(allInsights, 6);

  const COLORS = ['#3B82F6', '#8B5CF6', '#10B981', '#F59E0B', '#EF4444'];

  const handleSliceEnter = useCallback((index) => {
    setActiveCategorySlice(index);
  }, []);

  const handleSliceLeave = useCallback(() => {
    setActiveCategorySlice(null);
  }, []);
  const projection = useMemo(
    () => buildFinancialProjection(transactions, dashboardData?.total_balance),
    [transactions, dashboardData?.total_balance]
  );
  const recentTransactions = transactions.slice(0, 5);

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
      {/* Quick Insights */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Insights</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {quickInsights.map((insight, index) => (
            <div
              key={insight.id ?? `${insight.familyKey || insight.family}-${index}`}
              className="bg-gray-50 rounded-lg p-4"
            >
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <div
                    className={`w-2 h-2 rounded-full mt-2 ${
                      insight.priority === 'high'
                        ? 'bg-red-400'
                        : insight.priority === 'medium'
                        ? 'bg-yellow-400'
                        : 'bg-green-400'
                    }`}
                  />
                </div>
                <div className="ml-3">
                  <h4 className="text-sm font-medium text-gray-900">{insight.title}</h4>
                  <p className="text-sm text-gray-600 mt-1">{insight.description}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <BanknotesIcon className="h-8 w-8 text-green-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Total Balance</dt>
                <dd className="text-lg font-medium text-gray-900">
                  {formatCurrency(dashboardData?.total_balance || 0)}
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ArrowTrendingUpIcon className="h-8 w-8 text-red-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Monthly Spending (This Month)</dt>
                <dd className="text-lg font-medium text-gray-900">
                  {formatCurrency(dashboardData?.monthly_spending || 0)}
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CurrencyDollarIcon className="h-8 w-8 text-blue-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Transactions (This Month)</dt>
                <dd className="text-lg font-medium text-gray-900">
                  {dashboardData?.transaction_count || 0}
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ChartPieIcon className="h-8 w-8 text-purple-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Categories</dt>
                <dd className="text-lg font-medium text-gray-900">
                  {Object.keys(dashboardData?.top_categories || {}).length}
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Spending by Category */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Spending by Category (This Month)</h3>
          <p className="text-sm text-gray-500 mb-4">Breakdown of month-to-date spending.</p>
          <div className="h-80 lg:h-[26rem]">
            <ResponsiveContainer width="100%" height="100%" className="chart-no-clip">
              <PieChart margin={{ top: 24, right: 32, bottom: 24, left: 32 }}>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={120}
                  fill="#8884d8"
                  dataKey="value"
                  isAnimationActive={false}
                  labelLine={false}
                  label={renderCategoryLabel}
                >
                  {categoryData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={COLORS[index % COLORS.length]}
                      onMouseEnter={() => handleSliceEnter(index)}
                      onMouseLeave={handleSliceLeave}
                      style={{
                        transition: 'transform 180ms ease, filter 180ms ease',
                        transformOrigin: 'center',
                        transform: activeCategorySlice === index ? 'scale(0.96)' : 'scale(1)',
                        filter: activeCategorySlice === index ? 'brightness(1.15)' : 'none',
                        cursor: 'pointer',
                      }}
                    />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value) => formatCurrency(value)}
                  cursor={false}
                  contentStyle={{
                    backgroundColor: 'rgba(255,255,255,0.95)',
                    border: '1px solid #E5E7EB',
                    borderRadius: '10px',
                    boxShadow: '0 10px 30px rgba(15, 23, 42, 0.12)',
                    color: '#0F172A',
                  }}
                  wrapperStyle={{ outline: 'none' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent Transactions */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Transactions</h3>
          {transactionsLoading ? (
            <p className="text-sm text-gray-500">Loading most recent activity...</p>
          ) : transactionsError ? (
            <p className="text-sm text-red-500">{transactionsError}</p>
          ) : recentTransactions.length ? (
            <div className="space-y-3">
              {recentTransactions.map((transaction) => (
                <div key={transaction.id} className="flex items-center justify-between py-2">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      {transaction.merchant_name || transaction.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {new Date(transaction.date).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="text-sm font-medium text-gray-900">
                    {formatCurrency(Number(transaction.amount))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">No recent transactions to display.</p>
          )}
        </div>
      </div>

      <FinancialOutlookCard
        loading={transactionsLoading}
        error={transactionsError}
        projection={projection}
        formatCurrency={formatCurrency}
      />

    </div>
  );
};

export default Dashboard;

function FinancialOutlookCard({ loading, error, projection, formatCurrency }) {
  return (
    <div className="card">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Financial Outlook Projection</h3>
          <p className="text-sm text-gray-600">
            Forecasts your balance trajectory using income signals and spending trends.
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs uppercase tracking-wide text-gray-500">Confidence</p>
          <p className="text-sm font-semibold text-gray-900 capitalize">
            {projection?.incomeConfidence || '—'}
          </p>
          <p className="text-xs text-gray-500">{projection?.windowLabel || 'Awaiting data'}</p>
        </div>
      </div>

      {loading ? (
        <div className="mt-6 text-sm text-gray-500">Collecting transaction history...</div>
      ) : error ? (
        <div className="mt-6 text-sm text-red-500">{error}</div>
      ) : !projection?.hasData ? (
        <div className="mt-6 text-sm text-gray-500">
          {projection?.reason === 'insufficient'
            ? 'Not enough history for projections yet — check back after more transactions.'
            : 'Projection unavailable while we gather more data.'}
        </div>
      ) : (
        <>
          <div className="mt-6 h-96">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart
                data={projection.timeline}
                margin={{ top: 20, right: 20, left: 0, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="projectionCone" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#0EA5E9" stopOpacity={0.25} />
                    <stop offset="100%" stopColor="#6366F1" stopOpacity={0.05} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis
                  dataKey="label"
                  tick={{ fill: '#6B7280', fontSize: 12 }}
                  stroke="#E5E7EB"
                />
                <YAxis
                  width={72}
                  tick={{ fill: '#6B7280', fontSize: 12 }}
                  stroke="#E5E7EB"
                  tickFormatter={(value) => formatCurrency(value).replace('.00', '')}
                />
                <Tooltip content={<ProjectionTooltip formatCurrency={formatCurrency} />} />
                <Area
                  type="monotone"
                  dataKey="lowerBound"
                  stackId="confidence"
                  stroke="none"
                  fill="transparent"
                  isAnimationActive={false}
                />
                <Area
                  type="monotone"
                  dataKey="coneHeight"
                  stackId="confidence"
                  stroke="none"
                  fill="url(#projectionCone)"
                  isAnimationActive={false}
                />
                <Line
                  type="monotone"
                  dataKey="actualBalance"
                  stroke="#4F46E5"
                  strokeWidth={2.5}
                  dot={{ r: 3 }}
                  connectNulls
                />
                <Line
                  type="monotone"
                  dataKey="projectedBalance"
                  stroke="#0EA5E9"
                  strokeWidth={2.5}
                  strokeDasharray="5 5"
                  dot={{ r: 3 }}
                  connectNulls
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="rounded-lg border border-gray-200 bg-white/60 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1">
                Outlook Summary
              </p>
              <p className="text-sm text-gray-900">{projection.outlookSummary}</p>
              <p className="mt-3 text-xs text-gray-500">
                Expected income {formatCurrency(projection.expectedIncome || 0)} · spending{' '}
                {formatCurrency(projection.expectedSpending || 0)}
              </p>
            </div>

            <div className="rounded-lg border border-gray-200 bg-white/60 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1">
                Category Impact Snapshot
              </p>
              {projection.categoryImpacts?.length ? (
                <div className="space-y-2 text-sm text-gray-900">
                  {projection.categoryImpacts.map((item) => (
                    <div key={item.label} className="flex items-center justify-between">
                      <span>{item.label}</span>
                      <span className="font-medium">{item.percent}%</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500">No category insights available yet.</p>
              )}
            </div>

            <div className="rounded-lg border border-gray-200 bg-white/60 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1">
                Risk Indicators
              </p>
              {projection.riskIndicators?.length ? (
                <ul className="list-disc pl-4 text-sm text-gray-900 space-y-1">
                  {projection.riskIndicators.map((risk, index) => (
                    <li key={`${risk}-${index}`}>{risk}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-gray-500">No major risks detected.</p>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

const ProjectionTooltip = ({ active, payload, formatCurrency }) => {
  if (!active || !payload?.length) {
    return null;
  }
  const data = payload[0].payload;
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-3 text-xs shadow-lg space-y-1">
      <p className="font-semibold text-gray-900">{data.label}</p>
      {data.isProjected ? (
        <>
          <p className="text-gray-700">
            Expected Income: <span className="font-semibold">{formatCurrency(data.projectedIncome || 0)}</span>
          </p>
          <p className="text-gray-700">
            Expected Spending:{' '}
            <span className="font-semibold">{formatCurrency(data.projectedSpending || 0)}</span>
          </p>
          <p className="text-gray-700">
            Projected Net:{' '}
            <span className="font-semibold">{formatCurrency(data.projectedNet || 0)}</span>
          </p>
          <p className="text-gray-500">
            Confidence: <span className="capitalize">{data.incomeConfidence || 'low'}</span>
          </p>
          {typeof data.lowerBound === 'number' && typeof data.upperBound === 'number' && (
            <p className="text-gray-700">
              Potential Range:{' '}
              <span className="font-semibold">
                {formatCurrency(data.lowerBound)} → {formatCurrency(data.upperBound)}
              </span>
            </p>
          )}
        </>
      ) : (
        <>
          <p className="text-gray-700">
            Income: <span className="font-semibold">{formatCurrency(data.income || 0)}</span>
          </p>
          <p className="text-gray-700">
            Spending: <span className="font-semibold">{formatCurrency(data.spending || 0)}</span>
          </p>
          <p className="text-gray-700">
            Net Change:{' '}
            <span className="font-semibold">{formatCurrency(data.net || 0)}</span>
          </p>
          {data.topCategories?.length ? (
            <div className="text-gray-500">
              Top Categories:
              <ul className="list-disc pl-4">
                {data.topCategories.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {data.anomaly && (
            <p className="text-red-500">Anomaly detected — excluded from forecast volatility.</p>
          )}
        </>
      )}
    </div>
  );
};
