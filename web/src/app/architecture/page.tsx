'use client';

import { Sun, ArrowLeft, Database, Globe, Cpu, BarChart3, Zap, Building2, MapPin, DollarSign, Leaf, ChevronRight, Calendar } from 'lucide-react';
import Link from 'next/link';
import { ThemeToggle } from '@/components/ThemeToggle';

export default function ArchitecturePage() {
  return (
    <main className="max-w-5xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
      {/* Header */}
      <header className="mb-10">
        <div className="flex items-center justify-between mb-4">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Analyzer
          </Link>
          <ThemeToggle />
        </div>
        <div className="flex items-center gap-3 mb-3">
          <div className="p-2 bg-gradient-to-br from-solar-gold to-solar-orange rounded-xl">
            <Sun className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-gray-100">
              How It Works
            </h1>
            <p className="text-gray-500 dark:text-gray-400 text-sm sm:text-base">
              System architecture, data pipeline, and calculation methodology
            </p>
          </div>
        </div>
      </header>

      {/* Overview */}
      <Section title="System Overview" icon={<Globe className="w-5 h-5" />}>
        <p>
          The Airport Solar Potential Analyzer estimates rooftop solar energy generation and financial
          returns for buildings near the 30 busiest US airports. It combines geospatial building
          data with NREL solar irradiance models and real-world financial assumptions to produce
          per-building and aggregate solar potential estimates.
        </p>
        <div className="mt-6 grid sm:grid-cols-3 gap-4">
          <PipelineCard
            step="1"
            title="Identify Buildings"
            desc="Find all buildings within a given radius of each airport using Microsoft Building Footprints + OpenStreetMap data"
          />
          <PipelineCard
            step="2"
            title="Calculate Solar"
            desc="Estimate generation using NREL capacity factors, panel efficiency, and usable roof fraction"
          />
          <PipelineCard
            step="3"
            title="Financial Model"
            desc="Project 25-year returns with ITC, degradation, O&M costs, and discounted cash flow"
          />
        </div>
      </Section>

      {/* Data Sources */}
      <Section title="Data Sources" icon={<Database className="w-5 h-5" />}>
        <div className="space-y-4">
          <DataSource
            name="Microsoft Building Footprints"
            url="https://github.com/microsoft/USBuildingFootprints"
            desc="Machine-learning-derived building outlines from satellite imagery covering the entire US. Provides precise polygon geometries and roof areas for millions of buildings."
            citation="Microsoft, 2023"
          />
          <DataSource
            name="OpenStreetMap (Overpass API)"
            url="https://wiki.openstreetmap.org/wiki/Overpass_API"
            desc="Community-mapped building data supplements Microsoft footprints, capturing structures the ML model misses — especially metal-roofed warehouses, hangars, and cargo terminals common near airports."
            citation="OpenStreetMap Contributors"
          />
          <DataSource
            name="NREL Annual Technology Baseline (ATB)"
            url="https://atb.nrel.gov/electricity/2024/commercial_pv"
            desc="State-level AC capacity factors for commercial rooftop PV systems, ranging from 14.0% (Pacific Northwest) to 19.8% (Arizona/Southwest). Accounts for ~14% system losses including inverter efficiency, soiling, wiring, mismatch, and availability."
            citation="NREL, 2024"
          />
          <DataSource
            name="EPA eGRID"
            url="https://www.epa.gov/egrid"
            desc="State-level grid CO₂ emission rates (kg CO₂/kWh) used to calculate avoided carbon emissions from solar generation. Rates range from 0.120 (Washington, hydro-heavy) to 0.628 (Hawaii, oil-dependent)."
            citation="EPA eGRID, 2023"
          />
          <DataSource
            name="SEIA / Wood Mackenzie"
            url="https://www.seia.org/us-solar-market-insight"
            desc="Commercial rooftop PV installation cost benchmarks. Current assumption: $1.40/W for 200kW+ flat-roof systems."
            citation="SEIA/Wood Mackenzie, 2025"
          />
          <DataSource
            name="EIA Electricity Data"
            url="https://www.eia.gov/electricity/"
            desc="Average commercial electricity rates and residential consumption benchmarks (10,500 kWh/year average US household) used for revenue projections and 'homes powered' equivalency."
            citation="US EIA, 2024"
          />
        </div>
      </Section>

      {/* Calculation Pipeline */}
      <Section title="Calculation Pipeline" icon={<Cpu className="w-5 h-5" />}>
        <div className="space-y-6">
          <CalcStep
            num={1}
            title="Building Discovery"
            icon={<Building2 className="w-4 h-4" />}
            formulas={[
              'Filter buildings within radius of airport coordinates',
              'Merge Microsoft + OSM sources, remove overlapping duplicates (≥90% geometry intersection)',
              'Calculate roof area via UTM-projected polygon area (m²)',
              'Filter by minimum building size threshold',
            ]}
          />
          <CalcStep
            num={2}
            title="Solar Generation"
            icon={<Zap className="w-4 h-4" />}
            formulas={[
              'Usable Area = Total Roof Area × Usable Fraction (default 65%)',
              'Capacity (kW) = Usable Area × Panel Efficiency (W/m²) ÷ 1,000',
              'Annual Energy (kWh) = Capacity × 8,760 hours × Capacity Factor',
              'Year N Energy = Year 1 Energy × (1 − 0.5%)^(N−1)',
            ]}
          />
          <CalcStep
            num={3}
            title="Financial Model"
            icon={<DollarSign className="w-4 h-4" />}
            formulas={[
              'Gross Install Cost = Capacity × $1.40/W',
              'Net Cost = Gross Cost × (1 − 30% ITC)',
              'Annual Revenue = Energy × Electricity Price ($/kWh)',
              'Annual O&M = Capacity × $15/kW/year',
              'Payback = Net Cost ÷ (Annual Revenue − Annual O&M)',
              'NPV = −Net Cost + Σ(year 1→25) [(Revenue_n − O&M) ÷ (1 + 6%)^n]',
            ]}
          />
          <CalcStep
            num={4}
            title="Environmental Impact"
            icon={<Leaf className="w-4 h-4" />}
            formulas={[
              'CO₂ Avoided (tons/yr) = Annual Energy × State CO₂ Rate ÷ 1,000',
              'Lifetime CO₂ = Total 25-year Energy × State CO₂ Rate ÷ 1,000',
              'Homes Powered = Annual Energy ÷ 10,500 kWh/home',
            ]}
          />
        </div>
      </Section>

      {/* Key Assumptions */}
      <Section title="Key Assumptions" icon={<BarChart3 className="w-5 h-5" />}>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th className="text-left py-3 px-3 font-semibold text-gray-900 dark:text-gray-100">Parameter</th>
                <th className="text-left py-3 px-3 font-semibold text-gray-900 dark:text-gray-100">Default</th>
                <th className="text-left py-3 px-3 font-semibold text-gray-900 dark:text-gray-100">Range</th>
                <th className="text-left py-3 px-3 font-semibold text-gray-900 dark:text-gray-100">Source</th>
              </tr>
            </thead>
            <tbody className="text-gray-700 dark:text-gray-300">
              <AssumptionRow param="Panel Efficiency" def="200 W/m²" range="150–250 W/m²" source="Standard 20% commercial modules" />
              <AssumptionRow param="Usable Roof Fraction" def="65%" range="30–80%" source="NREL (Gagnon et al., 2016)" />
              <AssumptionRow param="Install Cost" def="$1.40/W" range="Fixed" source="SEIA/Wood Mackenzie 2025" />
              <AssumptionRow param="Federal ITC" def="30%" range="Fixed" source="Inflation Reduction Act, through 2032" />
              <AssumptionRow param="Degradation Rate" def="0.5%/yr" range="Fixed" source="NREL 2024 ATB" />
              <AssumptionRow param="O&M Cost" def="$15/kW/yr" range="Fixed" source="NREL 2024 ATB" />
              <AssumptionRow param="System Lifetime" def="25 years" range="Fixed" source="Industry standard" />
              <AssumptionRow param="Discount Rate" def="6%" range="Fixed" source="Commercial WACC benchmark" />
              <AssumptionRow param="Electricity Price" def="$0.13/kWh" range="$0.06–$0.25" source="EIA commercial average" />
              <AssumptionRow param="Capacity Factor" def="15.8% (US avg)" range="14.0–19.8%" source="NREL 2024 ATB, by state" />
            </tbody>
          </table>
        </div>
        <p className="mt-4 text-sm text-gray-500 dark:text-gray-400 italic">
          Parameters marked with a range can be adjusted using the sliders on the main analyzer page.
        </p>
      </Section>

      {/* Tech Stack */}
      <Section title="Technical Architecture" icon={<Cpu className="w-5 h-5" />}>
        <div className="grid sm:grid-cols-2 gap-6">
          <StackCard
            title="Frontend"
            items={[
              { label: 'Framework', value: 'Next.js 14 (React 18)' },
              { label: 'Styling', value: 'Tailwind CSS with dark mode' },
              { label: 'Maps', value: 'Leaflet + react-leaflet (Canvas renderer)' },
              { label: 'State', value: 'nuqs (URL-synced), SWR (data fetching)' },
              { label: 'Charts', value: 'Custom SVG components' },
            ]}
          />
          <StackCard
            title="Backend API"
            items={[
              { label: 'Framework', value: 'FastAPI (Python 3.12)' },
              { label: 'Server', value: 'Uvicorn ASGI' },
              { label: 'Data', value: 'Pre-cached GeoJSON/JSON per airport' },
              { label: 'Caching', value: 'LRU cache (64 airports) with deep copy' },
              { label: 'Security', value: 'Input validation, rate limiting, CSP headers' },
            ]}
          />
          <StackCard
            title="Data Pipeline"
            items={[
              { label: 'Building data', value: 'Microsoft Footprints + OSM Overpass API' },
              { label: 'Overlap removal', value: 'Shapely geometry intersection (≥90%)' },
              { label: 'Area calculation', value: 'UTM-projected polygon area' },
              { label: 'Caching', value: '30 airports pre-built as JSON' },
              { label: 'Coverage', value: '~230,000 buildings across 30 airports' },
            ]}
          />
          <StackCard
            title="Infrastructure"
            items={[
              { label: 'Frontend', value: 'Netlify (static export)' },
              { label: 'Backend API', value: 'Render (free tier)' },
              { label: 'Reverse proxy', value: 'Nginx (local dev)' },
              { label: 'Testing', value: 'pytest + httpx (155 tests)' },
              { label: 'CI/CD', value: 'Auto-deploy on git push' },
            ]}
          />
        </div>
      </Section>

      {/* API Endpoints */}
      <Section title="API Endpoints" icon={<Globe className="w-5 h-5" />}>
        <div className="space-y-3">
          <Endpoint method="GET" path="/api/airports" desc="List all 30 supported airports with coordinates, state, and metadata" />
          <Endpoint method="GET" path="/api/buildings/{code}" desc="Get buildings near an airport with full solar calculations. Supports radius, min_size, usable_pct, panel_eff, elec_price params" />
          <Endpoint method="GET" path="/api/compare" desc="Compare multiple airports side-by-side (up to 8). Returns per-airport summaries and building lists" />
          <Endpoint method="GET" path="/api/aggregate" desc="Aggregate totals across all 30 airports. Returns combined generation, revenue, and environmental impact" />
          <Endpoint method="GET" path="/api/capacity-factors" desc="NREL capacity factors by state, cached for 1 hour" />
          <Endpoint method="GET" path="/api/health" desc="Health check with uptime, version, and airport count" />
        </div>
      </Section>

      {/* Limitations */}
      <Section title="Known Limitations" icon={<BarChart3 className="w-5 h-5" />}>
        <ul className="space-y-2 text-gray-700 dark:text-gray-300">
          <li className="flex items-start gap-2">
            <ChevronRight className="w-4 h-4 mt-0.5 text-gray-400 flex-shrink-0" />
            <span><strong>Flat-roof assumption:</strong> All buildings are modeled as flat roofs. Actual tilt, orientation, and roof geometry are not considered.</span>
          </li>
          <li className="flex items-start gap-2">
            <ChevronRight className="w-4 h-4 mt-0.5 text-gray-400 flex-shrink-0" />
            <span><strong>No shading analysis:</strong> Obstructions from adjacent buildings, trees, or airport structures are not modeled.</span>
          </li>
          <li className="flex items-start gap-2">
            <ChevronRight className="w-4 h-4 mt-0.5 text-gray-400 flex-shrink-0" />
            <span><strong>Uniform capacity factors:</strong> A single state-level capacity factor is used for all buildings in that state, not site-specific GHI.</span>
          </li>
          <li className="flex items-start gap-2">
            <ChevronRight className="w-4 h-4 mt-0.5 text-gray-400 flex-shrink-0" />
            <span><strong>FAA glare considerations:</strong> Buildings near airports may face FAA glare restrictions on solar installations. This tool displays a glare risk indicator (high/moderate/low) based on distance from the airport, but does not perform a full FAA Solar Glare Hazard Analysis.</span>
          </li>
          <li className="flex items-start gap-2">
            <ChevronRight className="w-4 h-4 mt-0.5 text-gray-400 flex-shrink-0" />
            <span><strong>Static pricing:</strong> Electricity prices are assumed constant over the 25-year lifetime. No escalation rate is modeled.</span>
          </li>
          <li className="flex items-start gap-2">
            <ChevronRight className="w-4 h-4 mt-0.5 text-gray-400 flex-shrink-0" />
            <span><strong>Building data gaps:</strong> ML-derived footprints may miss some structures. OSM supplementation helps but doesn&apos;t guarantee 100% coverage.</span>
          </li>
        </ul>
      </Section>

      {/* Data Freshness */}
      <Section title="Data Freshness" icon={<Calendar className="w-5 h-5" />}>
        <p className="mb-4">
          All data sources are periodically updated to reflect the latest available figures.
          The most recent update was performed in <strong>June 2025</strong>.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th className="text-left py-2 px-3 font-semibold text-gray-900 dark:text-gray-100">Dataset</th>
                <th className="text-left py-2 px-3 font-semibold text-gray-900 dark:text-gray-100">Vintage</th>
                <th className="text-left py-2 px-3 font-semibold text-gray-900 dark:text-gray-100">Update Frequency</th>
              </tr>
            </thead>
            <tbody className="text-gray-700 dark:text-gray-300">
              <tr className="border-b border-gray-100 dark:border-gray-700">
                <td className="py-2 px-3">NREL ATB Capacity Factors</td>
                <td className="py-2 px-3 font-mono text-xs">2024</td>
                <td className="py-2 px-3 text-xs">Annual (solar resource doesn&apos;t change year-to-year)</td>
              </tr>
              <tr className="border-b border-gray-100 dark:border-gray-700">
                <td className="py-2 px-3">EPA eGRID CO₂ Rates</td>
                <td className="py-2 px-3 font-mono text-xs">2023</td>
                <td className="py-2 px-3 text-xs">Annual (published ~12 months after data year)</td>
              </tr>
              <tr className="border-b border-gray-100 dark:border-gray-700">
                <td className="py-2 px-3">EIA Electricity Prices</td>
                <td className="py-2 px-3 font-mono text-xs">2024</td>
                <td className="py-2 px-3 text-xs">Annual</td>
              </tr>
              <tr className="border-b border-gray-100 dark:border-gray-700">
                <td className="py-2 px-3">SEIA Install Costs</td>
                <td className="py-2 px-3 font-mono text-xs">Q1 2025</td>
                <td className="py-2 px-3 text-xs">Quarterly</td>
              </tr>
              <tr className="border-b border-gray-100 dark:border-gray-700">
                <td className="py-2 px-3">Building Footprints</td>
                <td className="py-2 px-3 font-mono text-xs">2023</td>
                <td className="py-2 px-3 text-xs">Cached; re-downloadable as source updates</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Section>

      {/* Footer */}
      <footer className="mt-12 py-6 border-t border-gray-200 dark:border-gray-700 text-center">
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium transition-colors"
        >
          <Sun className="w-4 h-4" />
          Back to Analyzer
        </Link>
      </footer>
    </main>
  );
}

/* ─── Sub-components ─── */

function Section({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <section className="mb-10">
      <div className="flex items-center gap-2 mb-4">
        <div className="text-primary-600 dark:text-primary-400">{icon}</div>
        <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">{title}</h2>
      </div>
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-5 sm:p-6 text-gray-700 dark:text-gray-300 text-sm leading-relaxed">
        {children}
      </div>
    </section>
  );
}

function PipelineCard({ step, title, desc }: { step: string; title: string; desc: string }) {
  return (
    <div className="relative bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4 border border-gray-100 dark:border-gray-600">
      <div className="absolute -top-3 left-4 bg-primary-600 text-white text-xs font-bold rounded-full w-6 h-6 flex items-center justify-center">
        {step}
      </div>
      <h3 className="font-semibold text-gray-900 dark:text-gray-100 mt-1 mb-1">{title}</h3>
      <p className="text-xs text-gray-600 dark:text-gray-400">{desc}</p>
    </div>
  );
}

function DataSource({ name, url, desc, citation }: { name: string; url: string; desc: string; citation: string }) {
  return (
    <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4 border border-gray-100 dark:border-gray-600">
      <div className="flex items-center justify-between mb-1">
        <a href={url} target="_blank" rel="noopener noreferrer" className="font-semibold text-primary-600 dark:text-primary-400 hover:underline">
          {name}
        </a>
        <span className="text-xs text-gray-400 dark:text-gray-500">{citation}</span>
      </div>
      <p className="text-xs text-gray-600 dark:text-gray-400">{desc}</p>
    </div>
  );
}

function CalcStep({ num, title, icon, formulas }: { num: number; title: string; icon: React.ReactNode; formulas: string[] }) {
  return (
    <div className="flex gap-4">
      <div className="flex-shrink-0 w-8 h-8 bg-primary-100 dark:bg-primary-900/40 text-primary-700 dark:text-primary-300 rounded-lg flex items-center justify-center font-bold text-sm">
        {num}
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-gray-400">{icon}</span>
          <h3 className="font-semibold text-gray-900 dark:text-gray-100">{title}</h3>
        </div>
        <div className="space-y-1">
          {formulas.map((f, i) => (
            <div key={i} className="font-mono text-xs text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-700/50 rounded px-3 py-1.5">
              {f}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function AssumptionRow({ param, def: defaultVal, range, source }: { param: string; def: string; range: string; source: string }) {
  return (
    <tr className="border-b border-gray-100 dark:border-gray-700">
      <td className="py-2.5 px-3 font-medium text-gray-900 dark:text-gray-100">{param}</td>
      <td className="py-2.5 px-3 font-mono text-xs">{defaultVal}</td>
      <td className="py-2.5 px-3 font-mono text-xs">{range}</td>
      <td className="py-2.5 px-3 text-xs text-gray-500 dark:text-gray-400">{source}</td>
    </tr>
  );
}

function StackCard({ title, items }: { title: string; items: { label: string; value: string }[] }) {
  return (
    <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4 border border-gray-100 dark:border-gray-600">
      <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">{title}</h3>
      <dl className="space-y-2 text-xs">
        {items.map((item, i) => (
          <div key={i} className="flex gap-2">
            <dt className="text-gray-500 dark:text-gray-400 w-24 flex-shrink-0 font-medium">{item.label}</dt>
            <dd className="text-gray-700 dark:text-gray-300">{item.value}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function Endpoint({ method, path, desc }: { method: string; path: string; desc: string }) {
  return (
    <div className="flex items-start gap-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 border border-gray-100 dark:border-gray-600">
      <span className="flex-shrink-0 bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300 text-xs font-bold px-2 py-0.5 rounded">
        {method}
      </span>
      <div>
        <code className="text-xs font-mono text-gray-900 dark:text-gray-100">{path}</code>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{desc}</p>
      </div>
    </div>
  );
}
