'use client';

import { Building2, Zap, DollarSign, MapPin, Home, Leaf, BarChart3, Download, TrendingUp, Shield, EyeOff, RotateCcw, Pencil, Trash2 } from 'lucide-react';
import { useState, useRef, useCallback, useMemo } from 'react';
import dynamic from 'next/dynamic';
import { MetricCard } from '@/components/MetricCard';
import { DataTable } from '@/components/DataTable';

const BuildingMap = dynamic(() => import('@/components/BuildingMap'), {
  ssr: false,
  loading: () => <div className="w-full h-[500px] bg-gray-100 dark:bg-gray-800 rounded-xl skeleton" />,
});

interface SingleAirportViewProps {
  data: any;
  radius: number;
  onExportCSV: () => void;
  selectedBuildings: any[];
  setSelectedBuildings: React.Dispatch<React.SetStateAction<any[]>>;
  hiddenCount?: number;
  onRestoreAll?: () => void;
  onDrawComplete?: (latlngs: { lat: number; lng: number }[]) => void;
  customBuildingCount?: number;
  onRemoveAllCustom?: () => void;
  onHideMultiple?: (buildings: any[]) => void;
}

export function SingleAirportView({ data, radius, onExportCSV, selectedBuildings, setSelectedBuildings, hiddenCount = 0, onRestoreAll, onDrawComplete, customBuildingCount = 0, onRemoveAllCustom, onHideMultiple }: SingleAirportViewProps) {
  const [focusBuilding, setFocusBuilding] = useState<any>(null);
  const mapRef = useRef<HTMLDivElement>(null);

  const bKey = (b: any) => `${b.lat}_${b.lon}_${b.area_m2}`;

  // Derived selectedKeys set for map/table highlighting
  const selectedKeys = useMemo(() => {
    return new Set(selectedBuildings.map(b => bKey(b)));
  }, [selectedBuildings]);

  // Toggle a building in/out of the selection
  const handleToggleSelect = useCallback((building: any) => {
    setSelectedBuildings((prev: any[]) => {
      const key = bKey(building);
      const exists = prev.some(b => bKey(b) === key);
      if (exists) {
        return prev.filter(b => bKey(b) !== key);
      } else {
        return [...prev, building];
      }
    });
  }, [setSelectedBuildings]);

  // Select/deselect a page of buildings (for table checkboxes)
  const handleSelectPage = useCallback((buildings: any[], selected: boolean) => {
    setSelectedBuildings((prev: any[]) => {
      const pageKeys = new Set(buildings.map(b => bKey(b)));
      if (selected) {
        // Add buildings not already selected
        const existingKeys = new Set(prev.map(b => bKey(b)));
        const toAdd = buildings.filter(b => !existingKeys.has(bKey(b)));
        return [...prev, ...toAdd];
      } else {
        return prev.filter(b => !pageKeys.has(bKey(b)));
      }
    });
  }, [setSelectedBuildings]);

  const handleLocate = useCallback((building: any) => {
    setFocusBuilding(building);
    // Scroll map into view
    if (mapRef.current) {
      mapRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    // Clear focus after animation
    setTimeout(() => setFocusBuilding(null), 1500);
  }, []);
  if (!data) return null;

  const totals = data.totals;
  const hasITC = totals?.itc_savings > 0;

  return (
    <>
      {/* Airport Header */}
      {data.airport && (
        <div className="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-700/50 rounded-2xl p-6 mb-6 flex items-center gap-4">
          <div className="text-4xl font-bold text-primary-600">{data.airport.code}</div>
          <div>
            <div className="text-xl font-semibold text-gray-900 dark:text-gray-100">{data.airport.name}</div>
            <div className="text-gray-500 dark:text-gray-400 flex items-center gap-1">
              <MapPin className="w-4 h-4" />
              {data.airport.state} &bull; {totals?.building_count || 0} buildings within {radius} km
            </div>
          </div>
        </div>
      )}

      {/* Hidden Buildings Banner */}
      {hiddenCount > 0 && (
        <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl px-4 py-3 mb-6 flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-amber-800 dark:text-amber-300">
            <EyeOff className="w-4 h-4" />
            <span>
              <strong>{hiddenCount}</strong> building{hiddenCount !== 1 ? 's' : ''} excluded
              {data._originalBuildingCount ? ` (${data._originalBuildingCount} total)` : ''}
            </span>
          </div>
          {onRestoreAll && (
            <button
              onClick={onRestoreAll}
              className="flex items-center gap-1.5 px-3 py-1 text-sm font-medium text-amber-700 dark:text-amber-300 hover:bg-amber-100 dark:hover:bg-amber-800/30 rounded-lg transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Restore All
            </button>
          )}
        </div>
      )}

      {/* Hero Metric */}
      {totals && (
        <div className="bg-gradient-to-br from-primary-600 to-purple-600 rounded-2xl p-8 mb-6 text-white text-center">
          <div className="text-5xl sm:text-6xl font-bold mb-2 animate-count">
            {totals.annual_mwh.toLocaleString()} MWh
          </div>
          <div className="text-lg opacity-90 mb-4">Total Annual Solar Energy Potential</div>
          <div className="flex flex-wrap justify-center gap-6 text-sm opacity-80">
            <span className="flex items-center gap-1">
              <Home className="w-4 h-4" />
              Powers {totals.homes_powered?.toLocaleString()} homes
            </span>
            <span className="flex items-center gap-1">
              <Leaf className="w-4 h-4" />
              Avoids {totals.co2_avoided_tons?.toLocaleString()} tons CO₂/yr
            </span>
            <span className="flex items-center gap-1">
              <TrendingUp className="w-4 h-4" />
              {totals.co2_avoided_lifetime_tons?.toLocaleString()} tons over 25 years
            </span>
          </div>
        </div>
      )}

      {/* Metrics Grid */}
      {totals && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <MetricCard icon={Building2} label="Buildings" value={totals.building_count} format="number" />
          <MetricCard icon={MapPin} label="Total Roof Area" value={totals.total_roof_area_m2 / 1e6} unit="km²" format="decimal" decimals={2} />
          <MetricCard icon={Zap} label="Peak Capacity" value={totals.capacity_mw} unit="MW" format="decimal" decimals={1} />
          <MetricCard icon={DollarSign} label="Annual Revenue" value={totals.annual_revenue / 1e6} unit="M" prefix="$" format="decimal" decimals={1} />
        </div>
      )}

      {/* Financial Metrics */}
      {totals && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-700">
            <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">Gross Install Cost</div>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              ${(totals.gross_install_cost / 1e6).toFixed(1)}M
            </div>
          </div>
          {hasITC && (
            <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-700">
              <div className="text-sm text-gray-500 dark:text-gray-400 mb-1 flex items-center gap-1">
                <Shield className="w-3.5 h-3.5" /> 30% ITC Savings
              </div>
              <div className="text-2xl font-bold text-green-600">
                -${(totals.itc_savings / 1e6).toFixed(1)}M
              </div>
            </div>
          )}
          <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-700">
            <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">Payback Period</div>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {totals.payback_years} years
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-700">
            <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">25-Year NPV</div>
            <div className={`text-2xl font-bold ${(totals.npv_25yr || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              ${((totals.npv_25yr || 0) / 1e6).toFixed(1)}M
            </div>
          </div>
        </div>
      )}

      {/* Map */}
      {data.buildings && data.buildings.length > 0 && (
        <div ref={mapRef} className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-4 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
              <MapPin className="w-5 h-5 text-gray-400" />
              Building Map
              <span className="text-sm font-normal text-gray-500 dark:text-gray-400">
                (click buildings to select)
              </span>
            </h2>
            <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
              <span className="flex items-center gap-1"><span className="w-3 h-3 bg-blue-500 rounded-sm" /> Selected</span>
              <span className="flex items-center gap-1"><span className="w-3 h-3 bg-violet-500 rounded-sm" /> Custom</span>
              <span className="flex items-center gap-1"><span className="w-3 h-3 bg-green-500 rounded-sm" /> Large ({'>'}50%)</span>
              <span className="flex items-center gap-1"><span className="w-3 h-3 bg-lime-500 rounded-sm" /> Medium (20-50%)</span>
              <span className="flex items-center gap-1"><span className="w-3 h-3 bg-yellow-400 rounded-sm" /> Smaller ({'<'}20%)</span>
              <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm border-2 border-red-500" /> High Glare</span>
              <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm border-2 border-amber-500" /> Mod. Glare</span>
            </div>
          </div>
          {/* Custom buildings banner */}
          {customBuildingCount > 0 && (
            <div className="flex items-center justify-between bg-violet-50 dark:bg-violet-900/20 border border-violet-200 dark:border-violet-800 rounded-lg px-3 py-2 mb-3 text-sm">
              <div className="flex items-center gap-2 text-violet-800 dark:text-violet-300">
                <Pencil className="w-3.5 h-3.5" />
                <span><strong>{customBuildingCount}</strong> custom building{customBuildingCount !== 1 ? 's' : ''} added</span>
              </div>
              {onRemoveAllCustom && (
                <button
                  onClick={onRemoveAllCustom}
                  className="flex items-center gap-1 px-2 py-0.5 text-xs font-medium text-violet-600 dark:text-violet-400 hover:bg-violet-100 dark:hover:bg-violet-800/30 rounded transition-colors"
                >
                  <Trash2 className="w-3 h-3" />
                  Remove All
                </button>
              )}
            </div>
          )}
          <BuildingMap
            center={[data.airport.lat, data.airport.lon]}
            buildings={data.buildings}
            airportCode={data.airport.code}
            radiusKm={radius}
            onBuildingClick={handleToggleSelect}
            focusBuilding={focusBuilding}
            onDrawComplete={onDrawComplete}
            selectedKeys={selectedKeys}
          />
        </div>
      )}

      {/* Data Table */}
      {data.buildings && data.buildings.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-gray-400" />
              Top Buildings by Potential
            </h2>
            <button
              onClick={onExportCSV}
              className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors"
            >
              <Download className="w-4 h-4" />
              Export CSV
            </button>
          </div>
          <DataTable
            buildings={data.buildings}
            state={data.airport.state}
            onRowClick={handleToggleSelect}
            onLocate={handleLocate}
            selectedKeys={selectedKeys}
            onToggleSelect={handleToggleSelect}
            onSelectPage={handleSelectPage}
          />
        </div>
      )}
    </>
  );
}
