import React, { useEffect, useMemo, useState } from 'react';
import { dashboardAPI } from '../api';
import {
  LightBulbIcon,
  BanknotesIcon,
  ChartBarSquareIcon,
  SparklesIcon,
  ClockIcon,
  GlobeAmericasIcon,
  ShieldCheckIcon,
  CurrencyDollarIcon,
} from '@heroicons/react/24/outline';

const Insights = () => {
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeDomain, setActiveDomain] = useState('all');

  useEffect(() => {
    dashboardAPI
      .getInsights()
      .then((data) => setInsights(data))
      .catch(() => setError('Failed to load insights'))
      .finally(() => setLoading(false));
  }, []);

  const domains = insights?.domains || [];

  const handleDomainSelect = (key) => {
    setActiveDomain(key);
  };

  const mergedInsights = useMemo(() => mergeSimilarInsights(domains), [domains]);
  const summaryChips = useMemo(() => buildSummaryChips(mergedInsights), [mergedInsights]);
  const sections = useMemo(() => buildAllDomainSections(mergedInsights), [mergedInsights]);
  const topDomainInsights = useMemo(
    () => sections.byDomain.slice(0, 3).flatMap((group) => group.insights),
    [sections]
  );
  const structuredDomains = useMemo(
    () => buildStructuredDomains(domains, mergedInsights),
    [domains, mergedInsights]
  );

  const filteredDomains =
    activeDomain === 'all'
      ? []
      : structuredDomains.filter((domain) => domain.key === activeDomain);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600" />
      </div>
    );
  }

  if (error) {
    return <div className="text-center text-red-600">{error}</div>;
  }

  return (
    <div className="space-y-6">
      <div className="bg-[#F8F9FF] rounded-lg border border-transparent p-6">
        <div className="flex flex-wrap justify-center gap-2">
          <FilterChip
            label="All Domains"
            active={activeDomain === 'all'}
            onClick={() => handleDomainSelect('all')}
            icon={LightBulbIcon}
            themeKey="default"
          />
          {domains.map((domain) => (
            <FilterChip
              key={domain.key}
              label={domain.name}
              active={activeDomain === domain.key}
              onClick={() => handleDomainSelect(domain.key)}
              icon={getDomainIcon(domain.key)}
              themeKey={domain.key}
            />
          ))}
        </div>
      </div>

      {activeDomain === 'all' && (
        <>
          {summaryChips.length > 0 && <SummaryChips chips={summaryChips} />}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Section
              title="Key Highlights"
              subtitle="Need-to-know insights across every domain."
              className="h-full"
            >
              {sections.keyHighlights.length ? (
                <div className="space-y-4">
                  {sections.keyHighlights.map((insight) => (
                    <InsightCard key={insight.id} insight={insight} emphasis />
                  ))}
                </div>
              ) : (
                <EmptyMessage message="No highlights yet — check back after new activity." />
              )}
            </Section>

            <Section
              title="Top Insights by Domain"
              subtitle="Curated highlights from each area."
              className="h-full"
            >
              {topDomainInsights.length ? (
                <div className="space-y-4">
                  {topDomainInsights.map((insight) => (
                    <InsightCard key={insight.id} insight={insight} compact />
                  ))}
                </div>
              ) : (
                <EmptyMessage message="Domain-specific insights will appear here soon." />
              )}
            </Section>

            <Section
              title="Cross-Domain Patterns"
              subtitle="Linked behaviors across categories."
              className="h-full"
            >
              {sections.crossDomain.length ? (
                <div className="space-y-4">
                  {sections.crossDomain.map((insight) => (
                    <InsightCard key={insight.id} insight={insight} />
                  ))}
                </div>
              ) : (
                <EmptyMessage message="We haven't detected cross-domain patterns yet." />
              )}
            </Section>
          </div>
        </>
      )}

      {activeDomain !== 'all' &&
        (filteredDomains.length ? (
          <div className="space-y-6">
            {filteredDomains.map((domain) => {
              const content = domainGrid(domain);
              return (
                <div key={domain.key}>
                  {content || (
                    <p className="text-sm text-[#6F7385]">
                      No insights in this domain yet.
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-12">
            <LightBulbIcon className="mx-auto h-12 w-12 text-[#6F7385]" />
            <h3 className="mt-2 text-sm font-medium text-[#1F2330]">No insights found</h3>
            <p className="mt-1 text-sm text-[#505869]">
              Connect your accounts and perform more transactions to unlock insights.
            </p>
          </div>
        ))}
    </div>
  );
};

export default Insights;

function FilterChip({ label, active, onClick, icon: Icon, themeKey = 'default' }) {
  const theme = DOMAIN_CHIP_COLORS[themeKey] || DOMAIN_CHIP_COLORS.default;
  const style = {
    backgroundColor: theme.bg,
    borderColor: theme.border,
    color: theme.text,
    fontWeight: 700,
    opacity: active ? 1 : 0.9,
  };
  const classes = active
    ? 'shadow-sm ring-1 ring-black/5'
    : 'hover:shadow-sm transition';
  return (
    <button
      onClick={onClick}
      style={style}
      className={`inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium border ${classes}`}
    >
      {Icon && <Icon className="w-4 h-4 mr-2" />}
      {label}
    </button>
  );
}

function getDomainIcon(key) {
  switch (key) {
    case 'spending_patterns':
      return ChartBarSquareIcon;
    case 'spending_trends':
      return ClockIcon;
    case 'optimization_rewards':
      return SparklesIcon;
    case 'behavior_lifestyle':
      return BanknotesIcon;
    case 'sustainability_local':
      return GlobeAmericasIcon;
    case 'financial_health':
      return ShieldCheckIcon;
    case 'income_cashflow':
      return CurrencyDollarIcon;
    default:
      return LightBulbIcon;
  }
}

function SummaryChips({ chips }) {
  return (
    <div className="bg-[#F4F1FF] rounded-lg shadow-sm border border-[#D6D9E6] p-4 flex flex-wrap gap-3">
      {chips.map((chip, index) => (
        <div
          key={index}
          className="px-3 py-1 bg-[#EDEAFF] text-[#5250C8] text-xs font-medium rounded-full border border-[#D6D9E6]"
        >
          <span className="font-semibold">{chip.label}: </span>
          {chip.value}
        </div>
      ))}
    </div>
  );
}

function InsightCard({ insight, emphasis = false, compact = false }) {
  const parsedData = parseInsightData(insight.data);
  const metrics = extractMetrics(parsedData);
  const context = parsedData.comparison_context || 'Based on recent activity.';
  const cta = getInsightCTA(insight.family);
  const palette = getInsightPalette(insight);

  return (
    <div
      className={`rounded-lg border p-4 shadow-sm transition ${
        emphasis ? 'ring-1 ring-primary-200' : ''
      } ${palette.container}`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getPriorityColor(insight.priority)}`}>
          {insight.priority} priority
        </span>
        <span className="text-xs text-gray-500">
          {new Date(insight.created_at).toLocaleDateString()}
        </span>
      </div>
      <h4 className="text-base font-semibold text-[#1F2330]">{insight.title}</h4>
      <p className="text-sm text-[#505869] mt-1">{insight.description}</p>
      {metrics.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2 text-xs">
          {metrics.map((metric, idx) => (
            <div key={idx} className={`px-2 py-1 rounded-md font-medium ${palette.metric}`}>
              {metric}
            </div>
          ))}
        </div>
      )}
      <p className="mt-3 text-xs text-[#6F7385]">{context}</p>
      {cta && !compact && (
        <button className="mt-3 text-xs font-semibold text-primary-600 hover:text-primary-700">
          {cta}
        </button>
      )}
    </div>
  );
}

function Section({ title, subtitle, children, className = '' }) {
  return (
    <div className={`rounded-lg shadow-sm border border-[#C7CBE4] bg-gradient-to-br from-[#EEF0FF] via-[#F8F9FF] to-white p-6 ${className}`}>
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          {subtitle && <p className="text-sm text-gray-600">{subtitle}</p>}
        </div>
      </div>
      {children}
    </div>
  );
}

function EmptyMessage({ message }) {
  return <p className="text-sm text-[#6F7385]">{message}</p>;
}

function domainGrid(domain) {
  const families = domain.families.filter((family) => family.insights.length);
  if (!families.length) {
    return null;
  }
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      {families.map((family) => (
        <div
          key={`${domain.key}-${family.key}`}
          className="border border-[#C7CBE4] rounded-lg bg-gradient-to-br from-[#EEF0FF] via-[#F8F9FF] to-white p-4 flex flex-col"
        >
          <div className="pb-3 mb-3 border-b border-[#ECEFFC]">
            <p className="text-sm font-semibold text-[#1F2330]">{family.name}</p>
            {family.description && (
              <p className="text-xs text-[#3F4759] mt-1">{family.description}</p>
            )}
          </div>
          <div className="space-y-3 flex-1">
            {family.insights.map((insight) => (
              <InsightCard key={insight.id} insight={insight} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

const DOMAIN_CHIP_COLORS = {
  default: {
    bg: '#F4F1FF',
    border: '#D6D9E6',
    text: '#5250C8',
  },
  spending_patterns: {
    bg: '#EDEAFF',
    border: '#D6D9E6',
    text: '#5250C8',
  },
  spending_trends: {
    bg: '#E3EEFF',
    border: '#C2D2FF',
    text: '#2D6BFF',
  },
  optimization_rewards: {
    bg: '#E6FBF2',
    border: '#BEEFDA',
    text: '#2BAA6A',
  },
  behavior_lifestyle: {
    bg: '#FFF4E3',
    border: '#F7DBB2',
    text: '#B7741A',
  },
  sustainability_local: {
    bg: '#F0FFF4',
    border: '#BDEFD1',
    text: '#2F8E57',
  },
  financial_health: {
    bg: '#FFEFF4',
    border: '#F5CEDB',
    text: '#CC3A56',
  },
  income_cashflow: {
    bg: '#EFF5FF',
    border: '#C7D9FF',
    text: '#2B4DA1',
  },
  long_term_goals: {
    bg: '#F7F3FF',
    border: '#D9CCFF',
    text: '#6D6AF2',
  },
};

const DOMAIN_PALETTES = {
  spending_patterns: {
    container: 'bg-[#EDEAFF] border-[#D6D9E6]',
    metric: 'bg-white/80 border-[#D6D9E6] text-[#5250C8]',
  },
  spending_trends: {
    container: 'bg-[#E3EEFF] border-[#C2D2FF]',
    metric: 'bg-white/80 border-[#C2D2FF] text-[#2D6BFF]',
  },
  optimization_rewards: {
    container: 'bg-[#E6FBF2] border-[#BEEFDA]',
    metric: 'bg-white/80 border-[#A5E2C7] text-[#2BAA6A]',
  },
  behavior_lifestyle: {
    container: 'bg-[#FFF4E3] border-[#F7DBB2]',
    metric: 'bg-white/80 border-[#F0C98C] text-[#B7741A]',
  },
  sustainability_local: {
    container: 'bg-[#F0FFF4] border-[#BDEFD1]',
    metric: 'bg-white/80 border-[#B3E3C7] text-[#2F8E57]',
  },
  financial_health: {
    container: 'bg-[#FFEFF4] border-[#F5CEDB]',
    metric: 'bg-white/80 border-[#F0B8CB] text-[#CC3A56]',
  },
  income_cashflow: {
    container: 'bg-[#EFF5FF] border-[#C7D9FF]',
    metric: 'bg-white/80 border-[#C0D0FF] text-[#2B4DA1]',
  },
  long_term_goals: {
    container: 'bg-[#F7F3FF] border-[#D9CCFF]',
    metric: 'bg-white/80 border-[#CEBFFF] text-[#6D6AF2]',
  },
  default: {
    container: 'bg-white border-[#D6D9E6]',
    metric: 'bg-[#F5F6FB] border-[#D6D9E6] text-[#505869]',
  },
};

function getInsightPalette(insight) {
  const key = insight.domainKey || insight.domain || 'default';
  return DOMAIN_PALETTES[key] || DOMAIN_PALETTES.default;
}

function mergeSimilarInsights(domains) {
  const rank = (priority) => ({ high: 0, medium: 1, low: 2 }[priority] ?? 3);
  const map = new Map();
  domains.forEach((domain) => {
    domain.families.forEach((family) => {
      family.insights.forEach((insight) => {
        const key = `${family.key}|${insight.title}`;
        if (!map.has(key) || rank(insight.priority) < rank(map.get(key).priority)) {
          map.set(key, {
            ...insight,
            domainKey: domain.key,
            domainName: domain.name,
            domainDescription: domain.description,
            familyKey: family.key,
            familyName: family.name,
            familyDescription: family.description,
          });
        }
      });
    });
  });
  return Array.from(map.values());
}

function buildSummaryChips(insights) {
  if (!insights.length) return [];
  const chips = [];
  const usedFamilies = new Set();
  const addChip = (label, value, key) => {
    if (!label || !value) return;
    if (chips.length >= 6) return;
    chips.push({ label, value });
    if (key) usedFamilies.add(key);
  };
  const findByFamily = (familyKey) => insights.find((i) => i.familyKey === familyKey);

  const favorite = findByFamily('favorite_merchants');
  if (favorite) {
    const merchant = favorite.title.replace(' is a Favorite', '').trim();
    addChip('Favorite Merchant', merchant || favorite.title, 'favorite_merchants');
  }

  const habit =
    findByFamily('habit_frequency') ||
    findByFamily('burst_spending');
  if (habit) {
    addChip('Consistent Habit', habit.title, habit.familyKey);
  }

  const local = findByFamily('local_support');
  if (local) {
    const data = parseInsightData(local.data);
    const pct = Number(data.local_percentage ?? 0);
    addChip('Local Impact', `${Math.round(pct)}% local spending`, 'local_support');
  }

  const consistency = findByFamily('consistency_score');
  if (consistency) {
    const data = parseInsightData(consistency.data);
    addChip('Consistency Score', `${Math.round(data.score || 0)}% stable`, 'consistency_score');
  }

  const saturation = findByFamily('category_saturation');
  if (saturation) {
    const data = parseInsightData(saturation.data);
    if (data.category) {
      addChip(
        'Top Category',
        `${data.category}: ${Math.round(Number(data.current_share || 0))}%`,
        'category_saturation'
      );
    }
  }

  const merchantSwitch = findByFamily('merchant_switching');
  if (merchantSwitch) {
    const data = parseInsightData(merchantSwitch.data);
    const label = data.new_merchant || data.newMerchant;
    if (label) {
      const visits = data.new_visits ?? data.newVisits;
      addChip('New Go-To', visits ? `${label} · ${visits} visits` : label, 'merchant_switching');
    }
  }

  const payment = findByFamily('payment_method_optimization');
  if (payment) {
    const data = parseInsightData(payment.data);
    const count = Number(data.transaction_count || 0);
    if (count) {
      addChip('Rewards Tip', `${count} big travel buys`, 'payment_method_optimization');
    }
  }

  const bundling = findByFamily('merchant_bundling');
  if (bundling) {
    const data = parseInsightData(bundling.data);
    const merchantCount = Number(data.merchant_count || 0);
    if (merchantCount) {
      addChip('Bundling Opportunity', `${merchantCount} merchants`, 'merchant_bundling');
    }
  }

  const lowWaste = findByFamily('low_waste_trend');
  if (lowWaste) {
    const data = parseInsightData(lowWaste.data);
    const count = Number(data.transaction_count || 0);
    if (count) {
      addChip('Low-Waste Buys', `${count} thrift visits`, 'low_waste_trend');
    }
  }

  const targetCount = Math.min(6, Math.max(4, chips.length));
  if (chips.length < targetCount) {
    insights.forEach((insight) => {
      if (chips.length >= targetCount) return;
      if (usedFamilies.has(insight.familyKey)) return;
      addChip(
        insight.familyName || formatLabel(insight.familyKey),
        insight.title,
        insight.familyKey
      );
    });
  }

  return chips;
}

function buildAllDomainSections(insights) {
  const MAX_TOTAL = 15;
  const count = () => selected.length;
  const pickTop = (filterFn, limit) => {
    const sorted = insights
      .filter(filterFn)
      .sort((a, b) => priorityRank(a) - priorityRank(b))
      .slice(0, limit);
    sorted.forEach((insight) => selected.add(insight.id));
    return sorted;
  };

  const selected = new Set();
  const priorityRank = (item) => ({ high: 0, medium: 1, low: 2 }[item.priority] ?? 3);

  const keyHighlights = pickTop(() => true, 5);
  const majorSpending = pickTop((i) => i.familyKey === 'category_trend', 3);
  const crossDomain = pickTop(
    (i) =>
      ['cross_user_affinity', 'delivery_vs_grocery', 'subscription_volume', 'subscription_price_change'].includes(
        i.familyKey
      ),
    3
  );

  const domainGroups = [];
  const domainOrder = [
    'spending_patterns',
    'spending_trends',
    'optimization_rewards',
    'behavior_lifestyle',
    'sustainability_local',
  ];
  domainOrder.forEach((domainKey) => {
    const domainInsights = insights
      .filter((i) => i.domainKey === domainKey && !selected.has(i.id))
      .sort((a, b) => priorityRank(a) - priorityRank(b))
      .slice(0, 2);
    domainInsights.forEach((insight) => selected.add(insight.id));
    if (domainInsights.length) {
      domainGroups.push({
        key: domainKey,
        title: getDomainTitle(domainKey),
        insights: domainInsights,
      });
    }
  });

  const totalUsed =
    keyHighlights.length + majorSpending.length + crossDomain.length + domainGroups.reduce((sum, group) => sum + group.insights.length, 0);
  if (totalUsed > MAX_TOTAL) {
    // truncate domain groups if over limit
    let excess = totalUsed - MAX_TOTAL;
    for (let i = domainGroups.length - 1; i >= 0 && excess > 0; i--) {
      const group = domainGroups[i];
      while (group.insights.length && excess > 0) {
        group.insights.pop();
        excess -= 1;
      }
      if (!group.insights.length) {
        domainGroups.splice(i, 1);
      }
    }
  }

  return { keyHighlights, majorSpending, crossDomain, byDomain: domainGroups };
}

function getDomainTitle(key) {
  switch (key) {
    case 'spending_patterns':
      return 'Spending Patterns';
    case 'spending_trends':
      return 'Spending Trends';
    case 'optimization_rewards':
      return 'Optimization & Rewards';
    case 'behavior_lifestyle':
      return 'Behavior & Lifestyle';
    case 'sustainability_local':
      return 'Sustainability & Local Impact';
    default:
      return key.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
  }
}

function buildStructuredDomains(domains, mergedInsights) {
  return domains.map((domain) => ({
    key: domain.key,
    name: domain.name,
    description: domain.description,
    families: domain.families.map((family) => ({
      key: family.key,
      name: family.name,
      description: family.description,
      insights: mergedInsights.filter(
        (insight) => insight.domainKey === domain.key && insight.familyKey === family.key
      ),
    })),
  }));
}

function extractMetrics(data) {
  if (!data) return [];
  const parsed = data;
  return Object.entries(parsed)
    .filter(([key]) => key !== 'comparison_context')
    .slice(0, 3)
    .map(([key, value]) => `${formatLabel(key)}: ${formatValue(value)}`);
}

function getInsightCTA() {
  return null;
}

function formatLabel(label) {
  return label
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatValue(value) {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'number') {
    if (Math.abs(value) >= 1000) {
      return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
    }
    return value.toLocaleString();
  }
  return value;
}

function parseInsightData(data) {
  if (!data) return {};
  if (typeof data === 'string') {
    try {
      return JSON.parse(data);
    } catch {
      return {};
    }
  }
  return data;
}

function getPriorityColor(priority) {
  switch (priority) {
    case 'high':
      return 'bg-[#FFE9EF] text-[#CC3A56] border-[#F8C7D4]';
    case 'medium':
      return 'bg-[#FFF5D5] text-[#D29E2F] border-[#F3D9A6]';
    case 'low':
      return 'bg-[#CFF8E4] text-[#2BAA6A] border-[#9FE9C4]';
    default:
      return 'bg-[#E1E6F6] text-[#505869] border-[#D6D9E6]';
  }
}

