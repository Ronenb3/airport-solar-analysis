'use client';

import { X, Zap, DollarSign, Leaf, MapPin, Ruler, Calendar, TrendingUp, Shield, EyeOff, Trash2, Pencil, Building2, AlertTriangle, CheckCircle, Info, Award, BarChart2, Tag } from 'lucide-react';

interface StateContext {
  elec_price?: number;
  net_metering?: { policy: string; label: string; detail: string };
  co2_rate?: number;
  rec_price_per_mwh?: number;
  lcfs_eligible?: boolean;
  ira_energy_community?: boolean;
  ira_adder_pct?: number;
}

interface BuildingDetailPanelProps {
  buildings: any[];
  onClose: () => void;
  onHide?: (buildings: any[]) => void;
  onRemoveCustom?: (id: string) => void;
  stateContext?: StateContext;
}

function GlareRiskBadge({ risk, hours }: { risk?: string; hours?: number | null }) {
  if (!risk) return null;
  const config: Record<string, { bg: string; text: string; icon: any; label: string }> = {
    high: { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-400', icon: AlertTriangle, label: 'High Glare Risk' },
    moderate: { bg: 'bg-amber-100 dark:bg-amber-900/30', text: 'text-amber-700 dark:text-amber-400', icon: AlertTriangle, label: 'Moderate Glare Risk' },
    low: { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-700 dark:text-green-400', icon: CheckCircle, label: 'Low Glare Risk' },
  };
  const c = config[risk] || config.low;
  const Icon = c.icon;
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${c.bg} ${c.text}`}>
      <Icon className="w-3 h-3" />
      {c.label}{hours != null ? ` · ${hours} hrs/yr` : ''}
    </span>
  );
}

function BuildingTypeBadge({ type }: { type?: string }) {
  if (!type) return null;
  const config: Record<string, { bg: string; text: string; label: string }> = {
    terminal:   { bg: 'bg-purple-100 dark:bg-purple-900/30', text: 'text-purple-700 dark:text-purple-400', label: '✈ Terminal' },
    hangar:     { bg: 'bg-blue-100 dark:bg-blue-900/30',   text: 'text-blue-700 dark:text-blue-400',   label: '🔧 Hangar' },
    cargo:      { bg: 'bg-orange-100 dark:bg-orange-900/30', text: 'text-orange-700 dark:text-orange-400', label: '📦 Cargo' },
    hotel:      { bg: 'bg-pink-100 dark:bg-pink-900/30',   text: 'text-pink-700 dark:text-pink-400',   label: '🏨 Hotel' },
    commercial: { bg: 'bg-gray-100 dark:bg-gray-700',      text: 'text-gray-700 dark:text-gray-300',   label: '🏢 Commercial' },
  };
  const c = config[type] || config.commercial;
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${c.bg} ${c.text}`}>
      {c.label}
    </span>
  );
}

function SplitIncentiveBadge({ level }: { level?: string }) {
  if (!level) return null;
  const config: Record<string, { bg: string; text: string; label: string; desc: string }> = {
    low:    { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-700 dark:text-green-400', label: 'No Split Incentive', desc: 'Owner-occupied — savings accrue to the decision-maker' },
    medium: { bg: 'bg-amber-100 dark:bg-amber-900/30', text: 'text-amber-700 dark:text-amber-400', label: 'Possible Split Incentive', desc: 'Building may be leased — verify ownership before investing' },
    high:   { bg: 'bg-red-100 dark:bg-red-900/30',   text: 'text-red-700 dark:text-red-400',   label: 'Split Incentive Risk', desc: 'Likely leased to 3rd party — landlord bears cost, tenant pays bills' },
  };
  const c = config[level] || config.medium;
  return (
    <div className={`${c.bg} rounded-lg p-2.5 text-xs border border-opacity-30`}>
      <div className={`font-semibold ${c.text}`}>{c.label}</div>
      <div className="text-gray-500 dark:text-gray-400 mt-0.5">{c.desc}</div>
    </div>
  );
}

function NetMeteringBadge({ netMetering }: { netMetering?: { policy: string; label: string; detail: string } }) {
  if (!netMetering) return null;
  const colorMap: Record<string, { bg: string; text: string; border: string }> = {
    full: { bg: 'bg-green-50 dark:bg-green-900/20', text: 'text-green-700 dark:text-green-400', border: 'border-green-200 dark:border-green-800' },
    reduced: { bg: 'bg-amber-50 dark:bg-amber-900/20', text: 'text-amber-700 dark:text-amber-400', border: 'border-amber-200 dark:border-amber-800' },
    varies: { bg: 'bg-gray-50 dark:bg-gray-700/50', text: 'text-gray-600 dark:text-gray-400', border: 'border-gray-200 dark:border-gray-700' },
    none: { bg: 'bg-gray-50 dark:bg-gray-700/50', text: 'text-gray-600 dark:text-gray-400', border: 'border-gray-200 dark:border-gray-700' },
  };
  const style = colorMap[netMetering.policy] || colorMap.varies;
  return (
    <div className={`${style.bg} ${style.border} border rounded-lg px-3 py-2 text-xs`}>
      <div className={`font-semibold ${style.text} flex items-center gap-1`}>
        <Zap className="w-3 h-3" />
        Net Metering: {netMetering.label}
      </div>
      <div className="text-gray-500 dark:text-gray-400 mt-0.5">{netMetering.detail}</div>
    </div>
  );
}

export function BuildingDetailPanel({ buildings, onClose, onHide, onRemoveCustom, stateContext }: BuildingDetailPanelProps) {
  if (!buildings || buildings.length === 0) return null;

  const isMulti = buildings.length > 1;
  const building = buildings[0]; // For single-building view

  // Combined stats for multi-selection
  const combined = isMulti ? {
    count: buildings.length,
    area_m2: buildings.reduce((s, b) => s + (b.area_m2 || 0), 0),
    usable_area_m2: buildings.reduce((s, b) => s + (b.solar?.usable_area_m2 || 0), 0),
    capacity_kw: buildings.reduce((s, b) => s + (b.solar?.capacity_kw || 0), 0),
    annual_mwh: buildings.reduce((s, b) => s + (b.solar?.annual_mwh || 0), 0),
    annual_revenue: buildings.reduce((s, b) => s + (b.solar?.annual_revenue || 0), 0),
    gross_install_cost: buildings.reduce((s, b) => s + (b.solar?.gross_install_cost || 0), 0),
    itc_savings: buildings.reduce((s, b) => s + (b.solar?.itc_savings || 0), 0),
    install_cost: buildings.reduce((s, b) => s + (b.solar?.install_cost || 0), 0),
    annual_om: buildings.reduce((s, b) => s + (b.solar?.annual_om || 0), 0),
    co2_avoided_tons: buildings.reduce((s, b) => s + (b.solar?.co2_avoided_tons || 0), 0),
    co2_avoided_lifetime_tons: buildings.reduce((s, b) => s + (b.solar?.co2_avoided_lifetime_tons || 0), 0),
    homes_powered: buildings.reduce((s, b) => s + (b.solar?.homes_powered || 0), 0),
    lifetime_mwh: buildings.reduce((s, b) => s + (b.solar?.lifetime_mwh || 0), 0),
  } : null;

  // Multi-building panel
  if (isMulti && combined) {
    const netRevenue = combined.annual_revenue - combined.annual_om;
    const payback = netRevenue > 0 ? combined.install_cost / netRevenue : 999;

    return (
      <div className="fixed right-0 top-0 h-full w-96 bg-white dark:bg-gray-900 shadow-2xl border-l border-gray-200 dark:border-gray-700 z-[1000] overflow-y-auto animate-slide-in">
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 p-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
            <Building2 className="w-5 h-5 text-blue-500" />
            {combined.count} Buildings Selected
          </h3>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            aria-label="Close panel"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <div className="p-4 space-y-4">
          {/* Roof Area */}
          <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <Ruler className="w-4 h-4 text-primary-600" />
              <span className="text-sm font-medium text-gray-900 dark:text-gray-100">Combined Roof Area</span>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-gray-500 dark:text-gray-400">Total Roof</span>
                <div className="font-semibold text-gray-900 dark:text-gray-100">{combined.area_m2.toLocaleString()} m²</div>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400">Usable Area</span>
                <div className="font-semibold text-gray-900 dark:text-gray-100">{combined.usable_area_m2.toLocaleString()} m²</div>
              </div>
            </div>
          </div>

          {/* Solar Generation */}
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <Zap className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-medium text-gray-900 dark:text-gray-100">Combined Solar Generation</span>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-gray-500 dark:text-gray-400">Peak Capacity</span>
                <div className="text-xl font-bold text-blue-700 dark:text-blue-400">{combined.capacity_kw.toLocaleString()} kW</div>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400">Annual Energy</span>
                <div className="text-xl font-bold text-blue-700 dark:text-blue-400">{combined.annual_mwh.toLocaleString()} MWh</div>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400">Lifetime Output</span>
                <div className="font-semibold text-gray-900 dark:text-gray-100">{combined.lifetime_mwh.toLocaleString()} MWh</div>
              </div>
            </div>
          </div>

          {/* Financials */}
          <div className="bg-green-50 dark:bg-green-900/20 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <DollarSign className="w-4 h-4 text-green-600" />
              <span className="text-sm font-medium text-gray-900 dark:text-gray-100">Combined Financials</span>
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">Gross Install Cost</span>
                <span className="font-semibold text-gray-900 dark:text-gray-100">${combined.gross_install_cost.toLocaleString()}</span>
              </div>
              {combined.itc_savings > 0 && (
                <div className="flex justify-between">
                  <span className="text-gray-500 dark:text-gray-400 flex items-center gap-1"><Shield className="w-3 h-3" /> 30% ITC Credit</span>
                  <span className="font-semibold text-green-600">-${combined.itc_savings.toLocaleString()}</span>
                </div>
              )}
              <div className="flex justify-between border-t border-green-200 dark:border-green-800 pt-2">
                <span className="text-gray-500 dark:text-gray-400">Net Cost</span>
                <span className="font-bold text-gray-900 dark:text-gray-100">${combined.install_cost.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">Annual Revenue</span>
                <span className="font-semibold text-green-700 dark:text-green-400">${combined.annual_revenue.toLocaleString()}/yr</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">Annual O&M</span>
                <span className="font-semibold text-gray-900 dark:text-gray-100">-${combined.annual_om.toLocaleString()}/yr</span>
              </div>
              <div className="flex justify-between border-t border-green-200 dark:border-green-800 pt-2">
                <span className="text-gray-700 dark:text-gray-300 font-medium flex items-center gap-1"><Calendar className="w-3 h-3" /> Est. Payback</span>
                <span className="font-bold text-green-700 dark:text-green-400">{payback < 100 ? payback.toFixed(1) : '—'} years</span>
              </div>
            </div>
          </div>

          {/* Net Metering */}
          <NetMeteringBadge netMetering={stateContext?.net_metering} />

          {/* Environmental */}
          <div className="bg-emerald-50 dark:bg-emerald-900/20 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <Leaf className="w-4 h-4 text-emerald-600" />
              <span className="text-sm font-medium text-gray-900 dark:text-gray-100">Combined Environmental Impact</span>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-gray-500 dark:text-gray-400">CO₂ Avoided/yr</span>
                <div className="font-semibold text-emerald-700 dark:text-emerald-400">{combined.co2_avoided_tons.toLocaleString()} tons</div>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400">Lifetime CO₂</span>
                <div className="font-semibold text-emerald-700 dark:text-emerald-400">{combined.co2_avoided_lifetime_tons.toLocaleString()} tons</div>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400">Homes Powered</span>
                <div className="font-semibold text-gray-900 dark:text-gray-100">{combined.homes_powered.toLocaleString()}</div>
              </div>
            </div>
          </div>

          {/* Exclude All button */}
          {onHide && (
            <button
              onClick={() => onHide(buildings)}
              className="w-full mt-2 flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/40 border border-red-200 dark:border-red-800 rounded-xl transition-colors"
            >
              <EyeOff className="w-4 h-4" />
              Exclude All {combined.count} Buildings
            </button>
          )}
        </div>
      </div>
    );
  }

  // Single-building panel (original)
  const solar = building.solar || {};
  const hasITC = solar.itc_savings > 0;

  return (
    <div className="fixed right-0 top-0 h-full w-96 bg-white dark:bg-gray-900 shadow-2xl border-l border-gray-200 dark:border-gray-700 z-[1000] overflow-y-auto animate-slide-in">
      {/* Header */}
      <div className="sticky top-0 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 p-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
          Building Details
          {building.isCustom && (
            <span className="text-xs font-medium bg-violet-100 dark:bg-violet-900/40 text-violet-700 dark:text-violet-300 px-2 py-0.5 rounded-full flex items-center gap-1">
              <Pencil className="w-3 h-3" /> Custom
            </span>
          )}
        </h3>
        <div className="flex items-center gap-1">
          {onHide && (
            <button
              onClick={() => onHide([building])}
              className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition-colors"
              aria-label="Exclude building"
              title="Exclude this building (false positive or duplicate)"
            >
              <EyeOff className="w-5 h-5" />
            </button>
          )}
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            aria-label="Close panel"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Location */}
        <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <MapPin className="w-4 h-4 text-primary-600" />
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">Location & Classification</span>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-gray-500 dark:text-gray-400">Distance</span>
              <div className="font-semibold text-gray-900 dark:text-gray-100">{building.distance_km?.toFixed(2)} km</div>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400">Coordinates</span>
              <div className="font-mono text-xs text-gray-700 dark:text-gray-300">
                {building.lat?.toFixed(4)}, {building.lon?.toFixed(4)}
              </div>
            </div>
          </div>
          <div className="flex flex-wrap gap-1.5 mt-2">
            <BuildingTypeBadge type={building.building_type} />
            <GlareRiskBadge risk={building.glare_risk} hours={building.glare_hours_per_year} />
          </div>
          {building.glare_worst_months?.length > 0 && (
            <div className="text-xs text-gray-500 dark:text-gray-400 mt-1.5">
              Peak glare months: {building.glare_worst_months.join(', ')}
            </div>
          )}
          {building.glare_description && building.glare_method === 'pvlib_specular' && (
            <div className="text-xs text-gray-400 dark:text-gray-500 mt-0.5 italic">{building.glare_description}</div>
          )}
        </div>

        {/* Roof Area */}
        <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <Ruler className="w-4 h-4 text-primary-600" />
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">Roof Area</span>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-gray-500 dark:text-gray-400">Total Roof</span>
              <div className="font-semibold text-gray-900 dark:text-gray-100">{building.area_m2?.toLocaleString()} m²</div>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400">Usable Area</span>
              <div className="font-semibold text-gray-900 dark:text-gray-100">
                {solar.usable_area_m2?.toLocaleString()} m²
              </div>
            </div>
          </div>
        </div>

        {/* Solar Generation */}
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <Zap className="w-4 h-4 text-blue-600" />
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">Solar Generation</span>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-gray-500 dark:text-gray-400">Peak Capacity</span>
              <div className="text-xl font-bold text-blue-700 dark:text-blue-400">{solar.capacity_kw?.toLocaleString()} kW</div>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400">Annual Energy</span>
              <div className="text-xl font-bold text-blue-700 dark:text-blue-400">{solar.annual_mwh?.toLocaleString()} MWh</div>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400">Capacity Factor</span>
              <div className="font-semibold text-gray-900 dark:text-gray-100">{((solar.capacity_factor || 0) * 100).toFixed(1)}%</div>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400">Lifetime Output</span>
              <div className="font-semibold text-gray-900 dark:text-gray-100">{solar.lifetime_mwh?.toLocaleString()} MWh</div>
            </div>
          </div>
        </div>

        {/* Financials */}
        <div className="bg-green-50 dark:bg-green-900/20 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <DollarSign className="w-4 h-4 text-green-600" />
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">Financial Analysis</span>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500 dark:text-gray-400">Gross Install Cost</span>
              <span className="font-semibold text-gray-900 dark:text-gray-100">
                ${solar.gross_install_cost?.toLocaleString()}
              </span>
            </div>
            {solar.faa_aip_applicable && solar.faa_aip_grant_potential > 0 && (
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400 flex items-center gap-1">
                  <Award className="w-3 h-3 text-amber-500" />
                  <span>FAA AIP grant potential</span>
                </span>
                <span className="font-semibold text-amber-600">${(solar.faa_aip_grant_potential || solar.faa_aip_grant || 0).toLocaleString()}</span>
              </div>
            )}
            {solar.faa_aip_applicable && (
              <div className="text-xs text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 rounded-lg px-2 py-1">
                ⚠ Grant potential only — requires 2–4 yr FAA application &amp; NEPA review. Not applied to base case costs.
              </div>
            )}
            {hasITC && (
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400 flex items-center gap-1">
                  <Shield className="w-3 h-3" /> ITC {Math.round((solar.itc_rate || 0.30) * 100)}%{solar.ira_adder > 0 ? ` (+${Math.round(solar.ira_adder*100)}% IRA)` : ''}
                </span>
                <span className="font-semibold text-green-600">-${solar.itc_savings?.toLocaleString()}</span>
              </div>
            )}
            <div className="flex justify-between border-t border-green-200 dark:border-green-800 pt-2">
              <span className="text-gray-500 dark:text-gray-400">Net Cost</span>
              <span className="font-bold text-gray-900 dark:text-gray-100">${solar.install_cost?.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500 dark:text-gray-400">Annual Revenue (electric)</span>
              <span className="font-semibold text-green-700 dark:text-green-400">
                ${solar.annual_revenue?.toLocaleString()}/yr
              </span>
            </div>
            {solar.annual_rec_revenue > 0 && (
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400 flex items-center gap-1">
                  <Tag className="w-3 h-3" /> RECs (${solar.rec_price_per_mwh}/MWh){solar.rec_price_volatile ? '⚠' : ''}
                </span>
                <span className="font-semibold text-green-600">+${solar.annual_rec_revenue?.toLocaleString()}/yr</span>
              </div>
            )}
            {solar.annual_demand_savings > 0 && (
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400 flex items-center gap-1">
                  <BarChart2 className="w-3 h-3" /> Demand charge savings*
                </span>
                <span className="font-semibold text-green-600">+${solar.annual_demand_savings?.toLocaleString()}/yr</span>
              </div>
            )}
            {solar.annual_lcfs_revenue > 0 && (
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-gray-400">LCFS credits (CA)</span>
                <span className="font-semibold text-green-600">+${solar.annual_lcfs_revenue?.toLocaleString()}/yr</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-gray-500 dark:text-gray-400">Annual O&M</span>
              <span className="font-semibold text-gray-900 dark:text-gray-100">-${solar.annual_om?.toLocaleString()}/yr</span>
            </div>
            <div className="flex justify-between border-t border-green-200 dark:border-green-800 pt-2">
              <span className="text-gray-700 dark:text-gray-300 font-medium flex items-center gap-1">
                <Calendar className="w-3 h-3" /> Payback Period
              </span>
              <div className="text-right">
                <span className="font-bold text-green-700 dark:text-green-400">{solar.payback_years} years</span>
                {solar.payback_years_base && solar.payback_years_base !== solar.payback_years && (
                  <div className="text-xs text-gray-400">{solar.payback_years_base}yr base case</div>
                )}
              </div>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-700 dark:text-gray-300 font-medium flex items-center gap-1">
                <TrendingUp className="w-3 h-3" /> 25-Year NPV
              </span>
              <span className={`font-bold ${(solar.npv_25yr || 0) >= 0 ? 'text-green-700 dark:text-green-400' : 'text-red-600'}`}>
                ${solar.npv_25yr?.toLocaleString()}
              </span>
            </div>
            {/* Scenario NPV breakdown */}
            {solar.scenario_npvs && (
              <div className="mt-1 rounded-lg bg-gray-50 dark:bg-gray-800 px-3 py-2 space-y-1">
                <div className="text-xs text-gray-500 dark:text-gray-400 font-medium mb-1">NPV by scenario</div>
                <div className="flex justify-between text-xs">
                  <span className="text-gray-500">Base (elec + ITC only)</span>
                  <span className="font-semibold text-gray-700 dark:text-gray-300">${(solar.scenario_npvs?.base || 0).toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-gray-500">With incentives</span>
                  <span className="font-semibold text-indigo-700 dark:text-indigo-400">${(solar.scenario_npvs?.incentives || 0).toLocaleString()}</span>
                </div>
                {solar.faa_aip_applicable && (
                  <div className="flex justify-between text-xs">
                    <span className="text-amber-600 dark:text-amber-400">⚠ With grants (FAA AIP)</span>
                    <span className="font-semibold text-amber-600 dark:text-amber-400">${(solar.scenario_npvs?.grants || 0).toLocaleString()}</span>
                  </div>
                )}
              </div>
            )}
            {/* Footnotes */}
            <div className="text-xs text-gray-400 dark:text-gray-500 space-y-0.5">
              {solar.annual_demand_savings > 0 && (
                <div>* Demand savings: 15% coincident peak assumed — verify with 15-min interval utility data.</div>
              )}
              {solar.rec_price_volatile && (
                <div>⚠ REC price: volatile market — actual contracted price may differ significantly.</div>
              )}
            </div>
          </div>
        </div>

        {/* LCOE Comparison */}
        {solar.lcoe_solar != null && (
          <div className="bg-indigo-50 dark:bg-indigo-900/20 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp className="w-4 h-4 text-indigo-600" />
              <span className="text-sm font-medium text-gray-900 dark:text-gray-100">LCOE Comparison</span>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm mb-3">
              <div>
                <span className="text-gray-500 dark:text-gray-400">Solar LCOE</span>
                <div className="text-xl font-bold text-blue-700 dark:text-blue-400">
                  ${solar.lcoe_solar?.toFixed(3)}<span className="text-xs font-normal">/kWh</span>
                </div>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400">Grid LCOE</span>
                <div className="text-xl font-bold text-red-600 dark:text-red-400">
                  ${solar.lcoe_grid?.toFixed(3)}<span className="text-xs font-normal">/kWh</span>
                </div>
              </div>
            </div>
            {solar.lcoe_savings_pct != null && (
              <div className={`text-center text-sm font-semibold px-3 py-1.5 rounded-lg ${
                solar.lcoe_savings_pct > 0
                  ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                  : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
              }`}>
                {solar.lcoe_savings_pct > 0
                  ? `Solar is ${solar.lcoe_savings_pct.toFixed(0)}% cheaper than grid`
                  : `Grid is ${Math.abs(solar.lcoe_savings_pct).toFixed(0)}% cheaper than solar`}
              </div>
            )}
            {solar.lifetime_savings != null && (
              <div className="flex justify-between text-sm mt-2 pt-2 border-t border-indigo-200 dark:border-indigo-800">
                <span className="text-gray-500 dark:text-gray-400">25-Year Savings vs Grid</span>
                <span className={`font-bold ${solar.lifetime_savings >= 0 ? 'text-green-700 dark:text-green-400' : 'text-red-600'}`}>
                  ${solar.lifetime_savings?.toLocaleString()}
                </span>
              </div>
            )}
            {solar.macrs_benefit > 0 && (
              <div className="flex justify-between text-sm mt-1">
                <span className="text-gray-500 dark:text-gray-400">MACRS Depreciation</span>
                <span className="font-semibold text-green-600">-${solar.macrs_benefit?.toLocaleString()}</span>
              </div>
            )}
            {solar.inverter_replacement_cost > 0 && (
              <div className="flex justify-between text-sm mt-1">
                <span className="text-gray-500 dark:text-gray-400">Inverter (Year {solar.inverter_replacement_year || 15})</span>
                <span className="font-semibold text-gray-900 dark:text-gray-100">${solar.inverter_replacement_cost?.toLocaleString()}</span>
              </div>
            )}
          </div>
        )}

        {/* Net Metering */}
        <NetMeteringBadge netMetering={stateContext?.net_metering} />

        {/* Incentives & Grants */}
        {(building.grant_programs?.length > 0 || building.ira_energy_community) && (
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <Award className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-medium text-gray-900 dark:text-gray-100">Incentives & Grants</span>
            </div>
            <div className="space-y-1.5">
              {building.grant_programs?.map((pg: string) => (
                <div key={pg} className="flex items-start gap-2 text-xs">
                  <CheckCircle className="w-3.5 h-3.5 text-blue-500 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700 dark:text-gray-300">{pg}</span>
                </div>
              ))}
              {building.ira_energy_community && (
                <div className="flex items-start gap-2 text-xs">
                  <CheckCircle className="w-3.5 h-3.5 text-blue-500 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700 dark:text-gray-300">IRA +{building.ira_adder_pct}% Energy Community bonus</span>
                </div>
              )}
              {solar.section_179d_benefit > 0 && (
                <div className="flex items-start gap-2 text-xs">
                  <CheckCircle className="w-3.5 h-3.5 text-blue-500 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700 dark:text-gray-300">§179D building deduction: +${solar.section_179d_benefit?.toLocaleString()}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Split Incentive / Ownership */}
        {building.split_incentive && (
          <SplitIncentiveBadge level={building.split_incentive} />
        )}

        {/* Environmental */}
        <div className="bg-emerald-50 dark:bg-emerald-900/20 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <Leaf className="w-4 h-4 text-emerald-600" />
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">Environmental Impact</span>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-gray-500 dark:text-gray-400">CO₂ Avoided/yr</span>
              <div className="font-semibold text-emerald-700 dark:text-emerald-400">
                {solar.co2_avoided_tons?.toLocaleString()} tons
              </div>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400">Lifetime CO₂</span>
              <div className="font-semibold text-emerald-700 dark:text-emerald-400">
                {solar.co2_avoided_lifetime_tons?.toLocaleString()} tons
              </div>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400">Homes Powered</span>
              <div className="font-semibold text-gray-900 dark:text-gray-100">{solar.homes_powered?.toLocaleString()}</div>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400">Grid CO₂ Rate</span>
              <div className="font-semibold text-gray-900 dark:text-gray-100">{solar.co2_rate_kg_kwh} kg/kWh</div>
            </div>
          </div>
        </div>

        {/* Assumptions */}
        <div className="text-xs text-gray-400 dark:text-gray-500 pt-2">
          <p>Panel degradation: {((solar.degradation_rate || 0.005) * 100).toFixed(1)}%/yr &bull; Discount rate: {((solar.discount_rate || 0.06) * 100)}%</p>
          <p>Install cost: ${solar.cost_per_watt}/W &bull; O&M: $15/kW/yr &bull; Rate escalation: {((solar.rate_escalation || 0.02) * 100).toFixed(0)}%/yr</p>
          <p>Inverter replacement at yr 15 &bull; MACRS 5-yr depreciation &bull; {solar.financing === 'loan' ? `Loan: ${(solar.loan_rate * 100).toFixed(1)}% / ${solar.loan_term}yr` : 'Cash purchase'}</p>
          {building.glare_method === 'pvlib_specular' && (
            <p>Glare: pvlib specular model (Sandia SAND2013-5426) &bull; FAA NASR runway headings</p>
          )}
          <p>REC: {building.rec_price_per_mwh || solar.rec_price_per_mwh || '—'}$/MWh &bull; Demand: ${solar.demand_charge_rate}/kW-mo {building.lcfs_eligible ? '· LCFS: $0.020/kWh' : ''}</p>
          <p>Sources: NREL 2024 ATB, SEIA 2025, EPA eGRID 2023, EIA 2024, OpenEI URDB, DSIRE 2024</p>
        </div>

        {/* Action Button */}
        {building.isCustom && onRemoveCustom ? (
          <button
            onClick={() => { onRemoveCustom(building.id); onClose(); }}
            className="w-full mt-2 flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/40 border border-red-200 dark:border-red-800 rounded-xl transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            Remove Custom Building
          </button>
        ) : onHide && (
          <button
            onClick={() => onHide([building])}
            className="w-full mt-2 flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/40 border border-red-200 dark:border-red-800 rounded-xl transition-colors"
          >
            <EyeOff className="w-4 h-4" />
            Exclude Building
          </button>
        )}
      </div>
    </div>
  );
}
