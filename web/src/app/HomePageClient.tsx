'use client';

import { useState, useCallback, useMemo, useEffect, useRef } from 'react';
import { useQueryState, parseAsInteger, parseAsFloat, parseAsString } from 'nuqs';
import useSWR from 'swr';
import Link from 'next/link';
import { Sun, RefreshCw, Settings2, Info, BookOpen } from 'lucide-react';
import { Slider } from '@/components/Slider';
import { Select } from '@/components/Select';
import { MultiSelect } from '@/components/MultiSelect';
import { useHiddenBuildings, buildingKey, recalcTotals } from '@/hooks/useHiddenBuildings';
import { useCustomBuildings } from '@/hooks/useCustomBuildings';
import { EquationsPanel } from '@/components/EquationsPanel';
import { ApiError } from '@/components/ApiError';
import { ThemeToggle } from '@/components/ThemeToggle';
import { BuildingDetailPanel } from '@/components/BuildingDetailPanel';
import { SingleAirportView } from '@/components/views/SingleAirportView';
import { CompareView } from '@/components/views/CompareView';
import { AggregateView } from '@/components/views/AggregateView';

// SWR fetcher with auto-retry for Render cold-start 502/504s
const fetcher = async (url: string, retries = 3): Promise<any> => {
  const res = await fetch(url);
  // 502 = Render not yet up, 504 = Netlify proxy timed out waiting for Render
  if ((res.status === 502 || res.status === 504) && retries > 0) {
    await new Promise(r => setTimeout(r, 5000));
    return fetcher(url, retries - 1);
  }
  if (!res.ok) {
    const error = new Error(`API error: ${res.status} ${res.statusText}`);
    (error as any).status = res.status;
    throw error;
  }
  return res.json();
};

interface Airport {
  code: string;
  name: string;
  state: string;
  lat: number;
  lon: number;
  elec_price?: number;
  net_metering?: { policy: string; label: string; detail: string };
}

type ViewMode = 'single' | 'compare' | 'aggregate';

export default function HomePage() {
  // URL-synced state (shareable)
  const [airportCode, setAirportCode] = useQueryState('airport', parseAsString.withDefault('ATL'));
  const [radius, setRadius] = useQueryState('radius', parseAsInteger.withDefault(5));
  const [minSize, setMinSize] = useQueryState('min_size', parseAsInteger.withDefault(500));
  const [viewMode, setViewMode] = useQueryState('view', parseAsString.withDefault('single'));
  const [compareCodes, setCompareCodes] = useQueryState('compare', parseAsString.withDefault(''));
  // Assumption sliders — now URL-synced for shareable links
  const [usablePct, setUsablePct] = useQueryState('usable', parseAsInteger.withDefault(65));
  const [panelEff, setPanelEff] = useQueryState('eff', parseAsInteger.withDefault(200));
  const [elecPriceQ, setElecPriceQ] = useQueryState('price', parseAsFloat.withDefault(0.12));
  const [rateEscalation, setRateEscalation] = useQueryState('escalation', parseAsFloat.withDefault(0.02));
  const [financing, setFinancing] = useQueryState('financing', parseAsString.withDefault('cash'));

  // Local UI state
  const [showEquations, setShowEquations] = useState(false);
  const [selectedBuildings, setSelectedBuildings] = useState<any[]>([]);

  // Hidden buildings (false positive / duplicate exclusion)
  const { hiddenCount, hideBuilding, hideMultiple, restoreAll, isHidden } = useHiddenBuildings(airportCode);

  // Compare mode: manage as array
  const compareArray = useMemo(() => {
    if (!compareCodes) return [];
    return compareCodes.split(',').filter(Boolean).map(c => c.trim().toUpperCase());
  }, [compareCodes]);

  const setCompareArray = useCallback((arr: string[]) => {
    setCompareCodes(arr.join(','));
  }, [setCompareCodes]);

  // Fetch airports list
  const { data: airports } = useSWR<Airport[]>('/api/airports', fetcher);

  // Warm up Render backend on first load — tracking vars for wake-up banner
  const [serverWaking, setServerWaking] = useState(false);
  const serverWakingRef = useRef(false);
  const mutateRef = useRef<() => void>(() => {});

  // Find airport center for custom buildings
  const airportCenter: [number, number] = useMemo(() => {
    if (!airports) return [33.6407, -84.4277]; // ATL default
    const apt = airports.find(a => a.code === airportCode);
    return apt ? [apt.lat, apt.lon] : [33.6407, -84.4277];
  }, [airports, airportCode]);

  // Auto-set electricity price when switching airports (state-specific price)
  const prevAirportRef = useRef(airportCode);
  useEffect(() => {
    if (!airports || airportCode === prevAirportRef.current) {
      prevAirportRef.current = airportCode;
      return;
    }
    prevAirportRef.current = airportCode;
    const apt = airports.find((a: Airport) => a.code === airportCode);
    if (apt?.elec_price) {
      // Round to nearest cent for slider step
      const rounded = Math.round(apt.elec_price * 100) / 100;
      setElecPriceQ(rounded);
    }
  }, [airports, airportCode, setElecPriceQ]);

  // Custom (user-drawn) buildings
  const { customBuildings, customCount, addBuilding, removeBuilding: removeCustomBuilding, removeAll: removeAllCustom } = useCustomBuildings(airportCode, airportCenter);

  // Build API URL
  const apiUrl = useMemo(() => {
    const params = `radius=${radius}&min_size=${minSize}&usable_pct=${(usablePct || 65) / 100}&panel_eff=${panelEff || 200}&elec_price=${elecPriceQ || 0.12}&rate_escalation=${rateEscalation || 0.02}&financing=${financing || 'cash'}`;
    if (viewMode === 'single') {
      return `/api/buildings/${airportCode}?${params}`;
    } else if (viewMode === 'compare' && compareCodes) {
      return `/api/compare?codes=${compareCodes}&${params}`;
    } else if (viewMode === 'aggregate') {
      return `/api/aggregate?${params}`;
    }
    return null;
  }, [viewMode, airportCode, compareCodes, radius, minSize, usablePct, panelEff, elecPriceQ, rateEscalation, financing]);

  const { data: rawData, error, isLoading, mutate } = useSWR(apiUrl, fetcher, {
    revalidateOnFocus: false,
    dedupingInterval: 5000,
    shouldRetryOnError: false,
  });

  // Keep mutateRef current so the ping effect can call it
  mutateRef.current = mutate;

  // Ping /api/health on mount; show waking banner + auto-retry data when server comes back
  useEffect(() => {
    let alive = true;
    const ping = async () => {
      try {
        const res = await fetch('/api/health');
        if ((res.status === 502 || res.status === 504) && alive) {
          serverWakingRef.current = true;
          setServerWaking(true);
          setTimeout(ping, 5000);
        } else if (alive) {
          const wasWaking = serverWakingRef.current;
          serverWakingRef.current = false;
          setServerWaking(false);
          if (wasWaking) mutateRef.current();
        }
      } catch {
        if (alive) {
          serverWakingRef.current = true;
          setServerWaking(true);
          setTimeout(ping, 5000);
        }
      }
    };
    ping();
    return () => { alive = false; };
  }, []);

  // Filter out hidden buildings, merge custom buildings, and recalculate totals
  const data = useMemo(() => {
    if (!rawData) return rawData;
    let buildings = rawData.buildings || [];
    const originalCount = buildings.length;

    // Filter hidden
    if (hiddenCount > 0) {
      buildings = buildings.filter((b: any) => !isHidden(b));
    }

    // Merge custom buildings with solar calculations
    if (customBuildings.length > 0 && rawData.totals) {
      const cf = rawData.totals.capacity_factor || 0.168;
      const usable = (usablePct || 65) / 100;
      const eff = panelEff || 200;
      const price = elecPriceQ || 0.12;

      const customWithSolar = customBuildings.map((cb: any) => {
        const usableArea = cb.area_m2 * usable;
        const capacityKw = usableArea * eff / 1000;
        const annualKwh = capacityKw * 8760 * cf;
        const grossCost = capacityKw * 1000 * 1.40;
        const itcSavings = grossCost * 0.30;
        const installCost = grossCost - itcSavings;
        const annualRevenue = annualKwh * price;
        const annualOm = capacityKw * 15;
        const payback = (annualRevenue - annualOm) > 0 ? installCost / (annualRevenue - annualOm) : 999;
        const co2Rate = rawData.state_context?.co2_rate || rawData.totals?.co2_rate_kg_kwh || 0.348; // Use state rate from API

        return {
          ...cb,
          solar: {
            usable_area_m2: Math.round(usableArea),
            capacity_kw: Math.round(capacityKw * 10) / 10,
            capacity_mw: Math.round(capacityKw / 100) / 10,
            annual_kwh: Math.round(annualKwh),
            annual_mwh: Math.round(annualKwh / 100) / 10,
            capacity_factor: cf,
            annual_revenue: Math.round(annualRevenue),
            gross_install_cost: Math.round(grossCost),
            itc_savings: Math.round(itcSavings),
            install_cost: Math.round(installCost),
            annual_om: Math.round(annualOm),
            payback_years: Math.round(payback * 10) / 10,
            npv_25yr: 0, // Simplified — not running full NPV client-side
            co2_avoided_tons: Math.round(annualKwh * co2Rate / 1000 * 10) / 10,
            co2_avoided_lifetime_tons: Math.round(annualKwh * 25 * co2Rate / 1000),
            homes_powered: Math.round(annualKwh / 10500),
            lifetime_mwh: Math.round(annualKwh * 25 / 1000),
            cost_per_watt: 1.40,
            itc_rate: 0.30,
            discount_rate: 0.06,
            degradation_rate: 0.005,
          },
        };
      });

      buildings = [...buildings, ...customWithSolar];
    }

    // Recalculate totals
    const newTotals = (hiddenCount > 0 || customBuildings.length > 0)
      ? recalcTotals(buildings, rawData.totals)
      : rawData.totals;

    return {
      ...rawData,
      buildings,
      totals: newTotals,
      _originalBuildingCount: hiddenCount > 0 ? originalCount : undefined,
    };
  }, [rawData, hiddenCount, isHidden, customBuildings, usablePct, panelEff, elecPriceQ]);

  // Airport options for select
  const airportOptions = useMemo(() => {
    if (!airports) return [];
    return airports.map((a) => ({
      value: a.code,
      label: `${a.code} - ${a.name}, ${a.state}`,
    }));
  }, [airports]);

  // Handle drawn building completion
  const handleDrawComplete = useCallback((latlngs: { lat: number; lng: number }[]) => {
    addBuilding(latlngs);
  }, [addBuilding]);

  // Export CSV
  const handleExportCSV = useCallback(() => {
    if (!data?.buildings) return;
    const headers = ['Rank', 'Area (m²)', 'Distance (km)', 'Capacity (kW)', 'Annual MWh', 'Revenue ($/yr)', 'Payback (yr)', 'NPV 25yr ($)', 'CO2 (t/yr)', 'Lat', 'Lon'];
    const rows = data.buildings.map((b: any, i: number) => [
      i + 1, b.area_m2, b.distance_km,
      b.solar?.capacity_kw || 0, b.solar?.annual_mwh || 0, b.solar?.annual_revenue || 0,
      b.solar?.payback_years || 0, b.solar?.npv_25yr || 0, b.solar?.co2_avoided_tons || 0,
      b.lat, b.lon,
    ]);
    const csv = [headers, ...rows].map((row) => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${airportCode}_solar_buildings.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data, airportCode]);

  return (
    <main className="max-w-[1600px] mx-auto px-4 py-6 sm:px-6 lg:px-8">
      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-gradient-to-br from-solar-gold to-solar-orange rounded-xl">
              <Sun className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-100">
                Airport Solar Potential Analyzer
              </h1>
              <p className="text-gray-500 dark:text-gray-400 text-sm sm:text-base">
                Analyze rooftop solar opportunities near major US airports
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Link
              href="/architecture"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              <BookOpen className="w-4 h-4" />
              <span className="hidden sm:inline">How It Works</span>
            </Link>
            <ThemeToggle />
          </div>
        </div>
      </header>

      {/* Controls Bar */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-4 mb-6">
        <div className="flex flex-wrap gap-4 items-end">
          {/* View Mode Tabs */}
          <div className="flex-shrink-0">
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">View</label>
            <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
              {(['single', 'compare', 'aggregate'] as ViewMode[]).map((mode) => (
                <button
                  key={mode}
                  onClick={() => { setViewMode(mode); setSelectedBuildings([]); }}
                  className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                    viewMode === mode
                      ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 shadow-sm'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
                  }`}
                >
                  {mode === 'single' ? 'Single' : mode === 'compare' ? 'Compare' : 'All Airports'}
                </button>
              ))}
            </div>
          </div>

          {/* Airport Select (Single mode) */}
          {viewMode === 'single' && (
            <div className="flex-1 min-w-[200px]">
              <Select
                label="Airport"
                value={airportCode}
                onChange={(v) => { setAirportCode(v); setSelectedBuildings([]); }}
                options={airportOptions}
              />
            </div>
          )}

          {/* Multi-Select (Compare mode) */}
          {viewMode === 'compare' && (
            <div className="flex-1 min-w-[280px]">
              <MultiSelect
                label="Compare Airports"
                values={compareArray}
                onChange={setCompareArray}
                options={airportOptions}
                placeholder="Search & select airports..."
                max={8}
              />
            </div>
          )}

          {/* Radius */}
          <div className="w-32">
            <Slider label="Radius" value={radius} onChange={(v) => setRadius(v)} min={2} max={10} step={1} unit="km" />
          </div>

          {/* Min Size */}
          <div className="w-36">
            <Slider label="Min Building" value={minSize} onChange={(v) => setMinSize(v)} min={200} max={5000} step={100} unit="m²" />
          </div>

          {/* Refresh */}
          <button
            onClick={() => mutate()}
            disabled={isLoading}
            className="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            aria-label="Refresh data"
          >
            <RefreshCw className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Assumption Sliders */}
        <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-2 mb-3">
            <Settings2 className="w-4 h-4 text-gray-400" />
            <span className="text-sm font-medium text-gray-600 dark:text-gray-300">Solar Assumptions</span>
            <button
              onClick={() => setShowEquations(!showEquations)}
              className="ml-auto text-xs text-primary-600 hover:text-primary-700 dark:text-primary-400 flex items-center gap-1"
            >
              <Info className="w-3.5 h-3.5" />
              {showEquations ? 'Hide equations' : 'Show equations'}
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Slider
              label="Usable Roof Area"
              value={usablePct || 65}
              onChange={(v) => setUsablePct(v)}
              min={30} max={80} step={5} unit="%"
              tooltip="Percentage of roof suitable for panels (excluding vents, HVAC, edges)"
            />
            <Slider
              label="Panel Efficiency"
              value={panelEff || 200}
              onChange={(v) => setPanelEff(v)}
              min={150} max={250} step={10} unit="W/m²"
              tooltip="Watts per square meter. 200 W/m² = standard 20% efficiency commercial panels."
            />
            <Slider
              label="Electricity Price"
              value={elecPriceQ || 0.12}
              onChange={(v) => setElecPriceQ(v)}
              min={0.06} max={0.25} step={0.01} unit="$/kWh"
              format={(v) => `$${v.toFixed(2)}`}
              tooltip="Average commercial electricity rate. US average ~$0.13/kWh (EIA 2024)."
            />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-3">
            <Slider
              label="Rate Escalation"
              value={rateEscalation || 0.02}
              onChange={(v) => setRateEscalation(v)}
              min={0} max={0.05} step={0.005} unit="%/yr"
              format={(v) => `${(v * 100).toFixed(1)}%`}
              tooltip="Annual electricity price increase. US historical average ~2%/yr (EIA)."
            />
            <div>
              <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Financing</label>
              <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
                {(['cash', 'loan'] as const).map((mode) => (
                  <button
                    key={mode}
                    onClick={() => setFinancing(mode)}
                    className={`flex-1 px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                      (financing || 'cash') === mode
                        ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 shadow-sm'
                        : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
                    }`}
                  >
                    {mode === 'cash' ? 'Cash Purchase' : 'Loan (6.5%/25yr)'}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {showEquations && (
          <EquationsPanel
            usablePct={usablePct || 65}
            panelEff={panelEff || 200}
            elecPrice={elecPriceQ || 0.12}
            capacityFactor={data?.totals?.capacity_factor || 0.168}
            rateEscalation={rateEscalation || 0.02}
          />
        )}
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="space-y-4">
          {serverWaking && (
            <div className="flex items-center gap-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl px-4 py-3 text-sm text-amber-800 dark:text-amber-300">
              <RefreshCw className="w-4 h-4 animate-spin flex-shrink-0" />
              <span><strong>Server is waking up</strong> — Render free tier spins down after inactivity. This takes 20–50 seconds. Retrying automatically…</span>
            </div>
          )}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-200 dark:border-gray-700">
                <div className="h-4 w-20 skeleton rounded mb-3" />
                <div className="h-8 w-24 skeleton rounded" />
              </div>
            ))}
          </div>
          <div className="flex items-center justify-center py-8">
            <div className="flex items-center gap-3 text-gray-500 dark:text-gray-400">
              <RefreshCw className="w-5 h-5 animate-spin" />
              <span>{serverWaking ? 'Waiting for server to start…' : 'Loading building data…'}</span>
            </div>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && !isLoading && <ApiError error={error} onRetry={mutate} />}

      {/* Views */}
      {viewMode === 'single' && data && !isLoading && (
        <SingleAirportView
          data={data}
          radius={radius}
          onExportCSV={handleExportCSV}
          selectedBuildings={selectedBuildings}
          setSelectedBuildings={setSelectedBuildings}
          hiddenCount={hiddenCount}
          onRestoreAll={restoreAll}
          onDrawComplete={handleDrawComplete}
          customBuildingCount={customCount}
          onRemoveAllCustom={removeAllCustom}
          onHideMultiple={hideMultiple}
          elecPrice={elecPriceQ || 0.12}
        />
      )}
      {viewMode === 'compare' && data && !isLoading && <CompareView data={data} />}
      {viewMode === 'aggregate' && data && !isLoading && <AggregateView data={data} />}

      {/* Building Detail Side Panel */}
      {selectedBuildings.length > 0 && (
        <BuildingDetailPanel
          buildings={selectedBuildings}
          onClose={() => setSelectedBuildings([])}
          onHide={(buildings: any[]) => {
            hideMultiple(buildings);
            setSelectedBuildings([]);
          }}
          onRemoveCustom={(id: string) => {
            removeCustomBuilding(id);
            setSelectedBuildings([]);
          }}
          stateContext={data?.state_context}
        />
      )}

      {/* Footer */}
      <footer className="mt-12 py-6 border-t border-gray-200 dark:border-gray-700 text-center text-sm text-gray-500 dark:text-gray-400">
        <p className="mb-2">
          Data sources: Microsoft Building Footprints &bull; OpenStreetMap &bull; NREL 2024 ATB &bull; EPA eGRID 2023 &bull; EIA 2024 &bull; SEIA 2025
        </p>
        <p className="text-xs">
          Estimates only. Actual solar potential depends on roof condition, orientation, shading, and local regulations.
          Includes 30% federal ITC, 0.5%/yr degradation, $15/kW/yr O&M, inverter replacement at yr 15, MACRS depreciation, and {((rateEscalation || 0.02) * 100).toFixed(0)}%/yr rate escalation.
          Consult a solar professional for accurate assessments.
        </p>
      </footer>
    </main>
  );
}
