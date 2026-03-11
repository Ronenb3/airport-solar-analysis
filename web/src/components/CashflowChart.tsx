'use client';

import { useMemo, useState } from 'react';
import {
  ComposedChart,
  Area,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';

interface YearlyData {
  year: number;
  grid_rate: number;
  grid_cost: number;
  solar_kwh: number;
  solar_cost: number;
  solar_revenue: number;
  savings: number;
  cumulative_savings: number;
  generation_mwh: number;
}

interface CashflowChartProps {
  yearlyData: YearlyData[];
  lcoe_solar: number;
  lcoe_grid: number;
  paybackYear: number | null;
  lifetimeSavings: number;
  /** Scale factor for display — 1 for individual building, 1e6 for airport totals */
  scale?: number;
}

type ChartView = 'costs' | 'cumulative' | 'lcoe';

export function CashflowChart({
  yearlyData,
  lcoe_solar,
  lcoe_grid,
  paybackYear,
  lifetimeSavings,
  scale = 1,
}: CashflowChartProps) {
  const [chartView, setChartView] = useState<ChartView>('costs');

  const isLargeScale = scale >= 1e6;
  const fmt = (v: number) => {
    if (isLargeScale) return `$${(v / 1e6).toFixed(1)}M`;
    if (Math.abs(v) >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
    if (Math.abs(v) >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
    return `$${v.toFixed(0)}`;
  };

  const data = useMemo(() => {
    return yearlyData.map((yd) => ({
      ...yd,
      // Running LCOE: cumulative cost / cumulative kWh up to this year
      grid_rate_display: yd.grid_rate,
    }));
  }, [yearlyData]);

  const lcoeData = useMemo(() => {
    let cumSolarCost = 0;
    let cumGridCost = 0;
    let cumKwh = 0;
    return yearlyData.map((yd) => {
      cumSolarCost += yd.solar_cost;
      cumGridCost += yd.grid_cost;
      cumKwh += yd.solar_kwh;
      return {
        year: yd.year,
        solar_lcoe: cumKwh > 0 ? cumSolarCost / cumKwh : 0,
        grid_lcoe: cumKwh > 0 ? cumGridCost / cumKwh : 0,
        grid_rate: yd.grid_rate,
      };
    });
  }, [yearlyData]);

  const savingsColor = lifetimeSavings >= 0 ? '#16a34a' : '#dc2626';

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;
    return (
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-3 text-xs">
        <div className="font-semibold text-gray-900 dark:text-gray-100 mb-1.5">Year {label}</div>
        {payload.map((entry: any, i: number) => (
          <div key={i} className="flex justify-between gap-4" style={{ color: entry.color }}>
            <span>{entry.name}:</span>
            <span className="font-mono font-medium">
              {chartView === 'lcoe'
                ? `$${entry.value.toFixed(4)}/kWh`
                : fmt(entry.value)}
            </span>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-4 mb-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            25-Year Financial Model
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Solar vs grid costs with {((yearlyData[0]?.grid_rate && yearlyData.length > 1)
              ? ((yearlyData[1].grid_rate / yearlyData[0].grid_rate - 1) * 100).toFixed(0)
              : '2')}% annual rate escalation
          </p>
        </div>
        {/* View toggle */}
        <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-0.5">
          {([
            { key: 'costs', label: 'Annual Costs' },
            { key: 'cumulative', label: 'Cumulative' },
            { key: 'lcoe', label: 'LCOE' },
          ] as { key: ChartView; label: string }[]).map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setChartView(key)}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                chartView === key
                  ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 shadow-sm'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Key stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg px-3 py-2">
          <div className="text-xs text-blue-600 dark:text-blue-400">Solar LCOE</div>
          <div className="text-lg font-bold text-blue-700 dark:text-blue-300">
            ${lcoe_solar.toFixed(3)}<span className="text-xs font-normal">/kWh</span>
          </div>
        </div>
        <div className="bg-red-50 dark:bg-red-900/20 rounded-lg px-3 py-2">
          <div className="text-xs text-red-600 dark:text-red-400">Grid LCOE</div>
          <div className="text-lg font-bold text-red-700 dark:text-red-300">
            ${lcoe_grid.toFixed(3)}<span className="text-xs font-normal">/kWh</span>
          </div>
        </div>
        <div className={`${lifetimeSavings >= 0 ? 'bg-green-50 dark:bg-green-900/20' : 'bg-red-50 dark:bg-red-900/20'} rounded-lg px-3 py-2`}>
          <div className={`text-xs ${lifetimeSavings >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
            25-Year Savings
          </div>
          <div className={`text-lg font-bold ${lifetimeSavings >= 0 ? 'text-green-700 dark:text-green-300' : 'text-red-700 dark:text-red-300'}`}>
            {fmt(lifetimeSavings)}
          </div>
        </div>
        <div className="bg-amber-50 dark:bg-amber-900/20 rounded-lg px-3 py-2">
          <div className="text-xs text-amber-600 dark:text-amber-400">Breakeven Year</div>
          <div className="text-lg font-bold text-amber-700 dark:text-amber-300">
            {paybackYear ? `Year ${paybackYear}` : '—'}
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="h-[320px]">
        <ResponsiveContainer width="100%" height="100%">
          {chartView === 'costs' ? (
            <ComposedChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis
                dataKey="year"
                tick={{ fontSize: 11 }}
                label={{ value: 'Year', position: 'insideBottom', offset: -2, fontSize: 11 }}
              />
              <YAxis
                tick={{ fontSize: 11 }}
                tickFormatter={(v) => fmt(v)}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="grid_cost" name="Grid Cost" fill="#ef4444" fillOpacity={0.6} />
              <Bar dataKey="solar_cost" name="Solar Cost" fill="#3b82f6" fillOpacity={0.6} />
              <Line
                dataKey="savings"
                name="Annual Savings"
                type="monotone"
                stroke="#16a34a"
                strokeWidth={2}
                dot={false}
              />
            </ComposedChart>
          ) : chartView === 'cumulative' ? (
            <ComposedChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis
                dataKey="year"
                tick={{ fontSize: 11 }}
                label={{ value: 'Year', position: 'insideBottom', offset: -2, fontSize: 11 }}
              />
              <YAxis
                tick={{ fontSize: 11 }}
                tickFormatter={(v) => fmt(v)}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <ReferenceLine y={0} stroke="#6b7280" strokeDasharray="4 4" />
              <Area
                dataKey="cumulative_savings"
                name="Cumulative Savings"
                type="monotone"
                stroke={savingsColor}
                fill={savingsColor}
                fillOpacity={0.15}
                strokeWidth={2}
              />
              {paybackYear && (
                <ReferenceLine
                  x={paybackYear}
                  stroke="#f59e0b"
                  strokeDasharray="4 4"
                  label={{
                    value: `Breakeven Yr ${paybackYear}`,
                    position: 'top',
                    fill: '#f59e0b',
                    fontSize: 11,
                  }}
                />
              )}
            </ComposedChart>
          ) : (
            <ComposedChart data={lcoeData} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis
                dataKey="year"
                tick={{ fontSize: 11 }}
                label={{ value: 'Year', position: 'insideBottom', offset: -2, fontSize: 11 }}
              />
              <YAxis
                tick={{ fontSize: 11 }}
                tickFormatter={(v) => `$${v.toFixed(2)}`}
                domain={['auto', 'auto']}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line
                dataKey="solar_lcoe"
                name="Solar LCOE"
                type="monotone"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={false}
              />
              <Line
                dataKey="grid_lcoe"
                name="Grid LCOE"
                type="monotone"
                stroke="#ef4444"
                strokeWidth={2}
                dot={false}
              />
              <Line
                dataKey="grid_rate"
                name="Grid Rate"
                type="monotone"
                stroke="#f97316"
                strokeWidth={1}
                strokeDasharray="5 5"
                dot={false}
              />
            </ComposedChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* Footer note */}
      <p className="mt-3 text-xs text-gray-400 dark:text-gray-500 italic">
        LCOE = total discounted costs ÷ total discounted energy (6% discount rate).
        Grid costs escalate at {((yearlyData[0]?.grid_rate && yearlyData.length > 1)
          ? ((yearlyData[1].grid_rate / yearlyData[0].grid_rate - 1) * 100).toFixed(0)
          : '2')}%/yr.
        Includes inverter replacement at year 15, MACRS depreciation (years 1-6), and 0.5%/yr panel degradation.
      </p>
    </div>
  );
}
