'use client';

import { useState, useCallback } from 'react';
import { TrendingUp, DollarSign, Zap, Award, Building2, BarChart2, ChevronDown, ChevronUp, Loader2, AlertTriangle } from 'lucide-react';

interface PortfolioBuilding {
  id: number;
  lat: number;
  lon: number;
  distance_km: number;
  area_m2: number;
  building_type: string;
  capacity_kw: number;
  annual_kwh: number;
  install_cost: number;
  npv_25yr: number;
  payback_years: number;
  lcoe_solar: number;
  annual_revenue: number;
  annual_rec_revenue: number;
  annual_demand_savings: number;
  faa_aip_applicable: boolean;
  ira_adder: number;
  npv_per_dollar: number;
}

interface PortfolioSummary {
  count: number;
  total_cost: number;
  total_npv: number;
  total_capacity_kw: number;
  total_capacity_mw: number;
  total_annual_kwh: number;
  total_annual_revenue: number;
  avg_payback_years: number;
  portfolio_roi_pct: number;
  budget_utilization_pct: number;
  remaining_budget: number;
  faa_aip_buildings_count: number;
  ira_adder_buildings_count: number;
}

interface OptimizeResult {
  airport: { code: string; name: string; state: string };
  budget: number;
  selected: PortfolioBuilding[];
  next_best: PortfolioBuilding[];
  summary: PortfolioSummary;
  all_candidates_count: number;
  elec_price_used: number;
}

interface PortfolioOptimizerProps {
  airportCode: string;
  elecPrice?: number;
  apiBase?: string;
}

const BUDGET_PRESETS = [
  { label: '$1M',   value: 1_000_000 },
  { label: '$5M',   value: 5_000_000 },
  { label: '$10M',  value: 10_000_000 },
  { label: '$25M',  value: 25_000_000 },
  { label: '$50M',  value: 50_000_000 },
  { label: '$100M', value: 100_000_000 },
];

const BUILDING_TYPE_LABELS: Record<string, string> = {
  terminal: '✈ Terminal',
  hangar:   '🔧 Hangar',
  cargo:    '📦 Cargo',
  hotel:    '🏨 Hotel',
  commercial: '🏢 Commercial',
};

function fmt$(n: number) {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
  return `$${n.toFixed(0)}`;
}

export function PortfolioOptimizer({ airportCode, elecPrice, apiBase = '' }: PortfolioOptimizerProps) {
  const [budget, setBudget] = useState(10_000_000);
  const [customBudget, setCustomBudget] = useState('');
  const [result, setResult] = useState<OptimizeResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showBuildings, setShowBuildings] = useState(false);

  const effectiveBudget = customBudget ? parseFloat(customBudget.replace(/[,$]/g, '')) || budget : budget;

  const runOptimizer = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        capital_budget: effectiveBudget.toString(),
        radius: '5',
        min_size: '500',
      });
      if (elecPrice) params.set('elec_price', elecPrice.toString());

      const url = `${apiBase}/api/optimize/${airportCode}?${params}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`API error ${res.status}`);
      const data: OptimizeResult = await res.json();
      setResult(data);
    } catch (e: any) {
      setError(e.message || 'Optimization failed');
    } finally {
      setLoading(false);
    }
  }, [airportCode, effectiveBudget, elecPrice, apiBase]);

  return (
    <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 px-5 py-4">
        <div className="flex items-center gap-2 text-white">
          <TrendingUp className="w-5 h-5" />
          <h3 className="text-base font-semibold">Portfolio Optimizer</h3>
        </div>
        <p className="text-indigo-100 text-xs mt-0.5">
          Maximize 25-year NPV within your capital budget — greedy knapsack algorithm
        </p>
      </div>

      <div className="p-5 space-y-4">
        {/* Budget Input */}
        <div>
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
            Capital Budget
          </label>
          <div className="flex flex-wrap gap-1.5 mb-2">
            {BUDGET_PRESETS.map(p => (
              <button
                key={p.value}
                onClick={() => { setBudget(p.value); setCustomBudget(''); }}
                className={`px-3 py-1 text-xs rounded-full font-medium transition-colors ${
                  budget === p.value && !customBudget
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Custom amount (e.g. $15,000,000)"
              value={customBudget}
              onChange={e => setCustomBudget(e.target.value)}
              className="flex-1 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400"
            />
            <button
              onClick={runOptimizer}
              disabled={loading}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-1.5"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <TrendingUp className="w-4 h-4" />}
              {loading ? 'Optimizing…' : 'Optimize'}
            </button>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="flex items-center gap-2 text-xs text-red-600 bg-red-50 dark:bg-red-900/20 rounded-lg p-3">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            {error}
          </div>
        )}

        {/* Results */}
        {result && !loading && (
          <div className="space-y-4">
            {/* Summary KPIs */}
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-indigo-50 dark:bg-indigo-900/20 rounded-xl p-3">
                <div className="text-xs text-gray-500 dark:text-gray-400">Portfolio NPV</div>
                <div className="text-xl font-bold text-indigo-700 dark:text-indigo-400">
                  {fmt$(result.summary.total_npv)}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">25-year value</div>
              </div>
              <div className="bg-green-50 dark:bg-green-900/20 rounded-xl p-3">
                <div className="text-xs text-gray-500 dark:text-gray-400">Capital Deployed</div>
                <div className="text-xl font-bold text-green-700 dark:text-green-400">
                  {fmt$(result.summary.total_cost)}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">{result.summary.budget_utilization_pct}% of {fmt$(result.budget)}</div>
              </div>
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-3">
                <div className="text-xs text-gray-500 dark:text-gray-400">Solar Capacity</div>
                <div className="text-xl font-bold text-blue-700 dark:text-blue-400">
                  {result.summary.total_capacity_mw.toFixed(2)} MW
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">{result.summary.count} buildings</div>
              </div>
              <div className="bg-amber-50 dark:bg-amber-900/20 rounded-xl p-3">
                <div className="text-xs text-gray-500 dark:text-gray-400">Portfolio ROI</div>
                <div className="text-xl font-bold text-amber-700 dark:text-amber-400">
                  {result.summary.portfolio_roi_pct > 999 ? '>999%' : `${result.summary.portfolio_roi_pct.toFixed(0)}%`}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">Avg {result.summary.avg_payback_years}yr payback</div>
              </div>
            </div>

            {/* Grant highlights */}
            {(result.summary.faa_aip_buildings_count > 0 || result.summary.ira_adder_buildings_count > 0) && (
              <div className="flex gap-2 flex-wrap">
                {result.summary.faa_aip_buildings_count > 0 && (
                  <div className="flex items-center gap-1.5 text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded-full px-3 py-1">
                    <Award className="w-3 h-3" />
                    {result.summary.faa_aip_buildings_count} FAA AIP eligible (90% federal)
                  </div>
                )}
                {result.summary.ira_adder_buildings_count > 0 && (
                  <div className="flex items-center gap-1.5 text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-full px-3 py-1">
                    <Award className="w-3 h-3" />
                    {result.summary.ira_adder_buildings_count} IRA energy community
                  </div>
                )}
              </div>
            )}

            {/* Annual stats */}
            <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-4 space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400 flex items-center gap-1">
                  <Zap className="w-3 h-3" /> Annual Generation
                </span>
                <span className="font-semibold text-gray-900 dark:text-gray-100">
                  {(result.summary.total_annual_kwh / 1000).toLocaleString(undefined, {maximumFractionDigits: 0})} MWh/yr
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400 flex items-center gap-1">
                  <DollarSign className="w-3 h-3" /> Annual Revenue (electric)
                </span>
                <span className="font-semibold text-green-700 dark:text-green-400">
                  {fmt$(result.summary.total_annual_revenue)}/yr
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">Electricity price used</span>
                <span className="font-semibold text-gray-600 dark:text-gray-400">
                  ${result.elec_price_used.toFixed(3)}/kWh
                </span>
              </div>
            </div>

            {/* Building list toggle */}
            <button
              onClick={() => setShowBuildings(!showBuildings)}
              className="w-full flex items-center justify-between text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 py-1"
            >
              <span className="flex items-center gap-1">
                <Building2 className="w-4 h-4" />
                {result.summary.count} selected buildings
              </span>
              {showBuildings ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>

            {showBuildings && (
              <div className="space-y-1.5 max-h-64 overflow-y-auto">
                {result.selected.slice(0, 20).map((b, i) => (
                  <div
                    key={b.id}
                    className="flex items-center justify-between text-xs bg-gray-50 dark:bg-gray-800 rounded-lg px-3 py-2"
                  >
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className="font-medium text-gray-900 dark:text-gray-100">
                          {BUILDING_TYPE_LABELS[b.building_type] || b.building_type}
                        </span>
                        <span className="text-gray-400">{b.area_m2.toLocaleString()}m²</span>
                        {b.faa_aip_applicable && (
                          <span className="text-blue-500 font-bold" title="FAA AIP eligible">✦</span>
                        )}
                      </div>
                      <div className="text-gray-400">{b.distance_km.toFixed(2)}km · {b.capacity_kw.toLocaleString()}kW</div>
                    </div>
                    <div className="text-right ml-3">
                      <div className="font-semibold text-green-700 dark:text-green-400">{fmt$(b.npv_25yr)}</div>
                      <div className="text-gray-400">{b.payback_years}yr payback</div>
                    </div>
                  </div>
                ))}
                {result.summary.count > 20 && (
                  <div className="text-center text-xs text-gray-400 py-1">
                    … and {result.summary.count - 20} more buildings
                  </div>
                )}
              </div>
            )}

            {/* Next best */}
            {result.next_best?.length > 0 && result.summary.remaining_budget > 0 && (
              <div className="border-t border-gray-200 dark:border-gray-700 pt-3">
                <div className="text-xs text-gray-500 dark:text-gray-400 mb-1.5">
                  Next-best (budget exhausted — {fmt$(result.summary.remaining_budget)} remaining):
                </div>
                {result.next_best.slice(0, 2).map(b => (
                  <div key={b.id} className="text-xs text-gray-500 dark:text-gray-400 flex justify-between py-0.5">
                    <span>{BUILDING_TYPE_LABELS[b.building_type]} {b.area_m2.toFixed(0)}m²</span>
                    <span>needs {fmt$(b.install_cost)}</span>
                  </div>
                ))}
              </div>
            )}

            <div className="text-xs text-gray-400 dark:text-gray-500">
              Algorithm: greedy NPV/cost ratio knapsack &bull; {result.all_candidates_count} viable candidates considered
            </div>
          </div>
        )}

        {!result && !loading && (
          <div className="text-center py-6 text-sm text-gray-400 dark:text-gray-500">
            <TrendingUp className="w-8 h-8 mx-auto mb-2 opacity-40" />
            Set a budget and click Optimize to find the highest-NPV building portfolio
          </div>
        )}
      </div>
    </div>
  );
}
