'use client';

import { useEffect, useMemo, useRef, useState, useCallback, memo } from 'react';
import { MapContainer, TileLayer, GeoJSON, Marker, Popup, Circle, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Pencil, Square, X, Check, Trash2, Plus } from 'lucide-react';

// Fix Leaflet default marker icon issue
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

interface Building {
  geometry: any;
  area_m2: number;
  distance_km: number;
  lat: number;
  lon: number;
  isCustom?: boolean;
  id?: string;
  glare_risk?: 'high' | 'moderate' | 'low';
  solar?: {
    capacity_kw: number;
    annual_mwh: number;
    annual_revenue: number;
    payback_years: number;
    co2_avoided_tons?: number;
  };
}

type DrawMode = 'none' | 'polygon' | 'rectangle';

interface BuildingMapProps {
  center: [number, number];
  buildings: Building[];
  airportCode: string;
  radiusKm?: number;
  onBuildingClick?: (building: Building) => void;
  selectedBuilding?: Building | null;
  focusBuilding?: Building | null;
  onDrawComplete?: (latlngs: { lat: number; lng: number }[]) => void;
  selectedKeys?: Set<string>;
}

// Component to fit map bounds to show all buildings
// Uses stable primitive deps to avoid re-fitting on every parent re-render
function MapBoundsUpdater({ center, buildings }: { center: [number, number]; buildings: Building[] }) {
  const map = useMap();
  const buildingsRef = useRef(buildings);
  buildingsRef.current = buildings;
  const centerLat = center[0];
  const centerLon = center[1];
  const buildingCount = buildings.length;
  
  useEffect(() => {
    const blds = buildingsRef.current;
    if (buildingCount > 0) {
      const lats = blds.map(b => b.lat).concat([centerLat]);
      const lons = blds.map(b => b.lon).concat([centerLon]);
      const bounds = L.latLngBounds(
        [Math.min(...lats), Math.min(...lons)],
        [Math.max(...lats), Math.max(...lons)]
      );
      map.fitBounds(bounds, { padding: [30, 30], maxZoom: 15 });
    } else {
      map.setView([centerLat, centerLon], 14);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [map, centerLat, centerLon, buildingCount]);
  
  return null;
}

// Component to fly to a focused building
function FlyToBuilding({ building }: { building: Building | null | undefined }) {
  const map = useMap();
  
  useEffect(() => {
    if (building) {
      map.flyTo([building.lat, building.lon], 18, { duration: 0.8 });
    }
  }, [map, building]);
  
  return null;
}

// Drawing handler component
function DrawingHandler({ mode, points, setPoints, onComplete, onCompleteWith, onCancel }: {
  mode: DrawMode;
  points: L.LatLng[];
  setPoints: (pts: L.LatLng[]) => void;
  onComplete: () => void;
  onCompleteWith: (pts: L.LatLng[]) => void;
  onCancel: () => void;
}) {
  const map = useMap();
  const rectStartRef = useRef<L.LatLng | null>(null);
  const previewLayerRef = useRef<L.Layer | null>(null);

  // Clean up preview on unmount or mode change
  useEffect(() => {
    return () => {
      if (previewLayerRef.current) {
        map.removeLayer(previewLayerRef.current);
        previewLayerRef.current = null;
      }
    };
  }, [map, mode]);

  useMapEvents({
    click(e: L.LeafletMouseEvent) {
      if (mode === 'polygon') {
        setPoints([...points, e.latlng]);
      } else if (mode === 'rectangle') {
        if (!rectStartRef.current) {
          rectStartRef.current = e.latlng;
          setPoints([e.latlng]);
        } else {
          // Complete rectangle - pass corners directly to avoid stale state
          const start = rectStartRef.current;
          const end = e.latlng;
          const corners = [
            L.latLng(start.lat, start.lng),
            L.latLng(start.lat, end.lng),
            L.latLng(end.lat, end.lng),
            L.latLng(end.lat, start.lng),
          ];
          rectStartRef.current = null;
          onCompleteWith(corners);
        }
      }
    },
    mousemove(e: L.LeafletMouseEvent) {
      // Live preview
      if (previewLayerRef.current) {
        map.removeLayer(previewLayerRef.current);
        previewLayerRef.current = null;
      }

      if (mode === 'polygon' && points.length > 0) {
        const latlngs = [...points, e.latlng];
        previewLayerRef.current = L.polyline(latlngs, {
          color: '#3b82f6',
          weight: 2,
          dashArray: '6, 4',
        }).addTo(map);
      } else if (mode === 'rectangle' && rectStartRef.current) {
        const start = rectStartRef.current;
        const end = e.latlng;
        const bounds = L.latLngBounds(start, end);
        previewLayerRef.current = L.rectangle(bounds, {
          color: '#3b82f6',
          weight: 2,
          fillOpacity: 0.15,
          dashArray: '6, 4',
        }).addTo(map);
      }
    },
    keydown(e: any) {
      if (e.originalEvent.key === 'Escape') {
        onCancel();
      } else if (e.originalEvent.key === 'Enter' && mode === 'polygon' && points.length >= 3) {
        onComplete();
      }
    },
  });

  // Render placed polygon points as markers
  useEffect(() => {
    if (mode !== 'polygon') return;
    const markers: L.CircleMarker[] = [];
    points.forEach((p) => {
      const marker = L.circleMarker(p, {
        radius: 5,
        color: '#3b82f6',
        fillColor: '#fff',
        fillOpacity: 1,
        weight: 2,
      }).addTo(map);
      markers.push(marker);
    });

    // Draw lines between points
    let polyline: L.Polyline | null = null;
    if (points.length >= 2) {
      polyline = L.polyline(points, {
        color: '#3b82f6',
        weight: 2,
      }).addTo(map);
    }

    return () => {
      markers.forEach(m => map.removeLayer(m));
      if (polyline) map.removeLayer(polyline);
    };
  }, [map, mode, points]);

  return null;
}

// Custom airport icon
const airportIcon = new L.DivIcon({
  html: `
    <div style="
      background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
      width: 32px;
      height: 32px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 2px 8px rgba(0,0,0,0.3);
      border: 2px solid white;
    ">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="white">
        <path d="M21 16v-2l-8-5V3.5A1.5 1.5 0 0011.5 2h-1A1.5 1.5 0 009 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L12 19v-5.5l8 2.5z"/>
      </svg>
    </div>
  `,
  className: '',
  iconSize: [32, 32],
  iconAnchor: [16, 16],
});

function BuildingMapComponent({ center, buildings, airportCode, radiusKm = 5, onBuildingClick, selectedBuilding, focusBuilding, onDrawComplete, selectedKeys }: BuildingMapProps) {
  const renderer = useMemo(() => L.canvas({ padding: 0.5 }), []);
  const [drawMode, setDrawMode] = useState<DrawMode>('none');
  const [drawPoints, setDrawPoints] = useState<L.LatLng[]>([]);

  const maxArea = useMemo(() => {
    return buildings.length > 0 ? Math.max(...buildings.map(b => b.area_m2)) : 1;
  }, [buildings]);

  const getColor = (area: number, isCustom?: boolean) => {
    if (isCustom) return '#8b5cf6'; // Purple for custom buildings
    const ratio = area / maxArea;
    if (ratio > 0.5) return '#22c55e';
    if (ratio > 0.2) return '#84cc16';
    return '#facc15';
  };

  const getBorderColor = (glareRisk?: string, isCustom?: boolean) => {
    if (isCustom) return '#7c3aed';
    if (glareRisk === 'high') return '#ef4444';   // red
    if (glareRisk === 'moderate') return '#f59e0b'; // amber
    return '#000';
  };

  const styleFeature = (feature: any) => {
    const area = feature.properties?.area_m2 || 1000;
    const isCustom = feature.properties?.isCustom;
    const glareRisk = feature.properties?.glare_risk;
    const bKey = `${feature.properties?.lat}_${feature.properties?.lon}_${feature.properties?.area_m2}`;
    const isSelected = selectedKeys && selectedKeys.has(bKey);
    return {
      fillColor: isSelected ? '#3b82f6' : getColor(area, isCustom),
      color: isSelected ? '#1d4ed8' : getBorderColor(glareRisk, isCustom),
      weight: isSelected ? 3 : (glareRisk === 'high' || glareRisk === 'moderate') ? 2.5 : isCustom ? 2 : 1,
      fillOpacity: isSelected ? 0.85 : 0.7,
    };
  };

  const onEachFeature = (feature: any, layer: L.Layer) => {
    const props = feature.properties;
    if (props) {
      const customLabel = props.isCustom ? '<br/><em style="color:#8b5cf6">Custom building</em>' : '';
      const glareLabel = props.glare_risk === 'high'
        ? '<br/><span style="color:#ef4444">⚠ High FAA glare risk</span>'
        : props.glare_risk === 'moderate'
        ? '<br/><span style="color:#f59e0b">⚠ Moderate glare risk</span>'
        : '';
      layer.bindTooltip(
        `<div style="font-family: system-ui; font-size: 12px;">
          <strong>${props.area_m2?.toLocaleString()} m²</strong><br/>
          ${props.distance_km?.toFixed(2)} km from airport<br/>
          ${props.solar ? `${props.solar.capacity_kw?.toLocaleString()} kW` : ''}
          ${glareLabel}
          ${customLabel}
        </div>`,
        { sticky: true }
      );
      if (drawMode === 'none') {
        const findBuilding = () => buildings.find(
          (b) => b.lat === props.lat && b.lon === props.lon && b.area_m2 === props.area_m2
        );
        if (onBuildingClick) {
          (layer as any).on('click', () => {
            const building = findBuilding();
            if (building) onBuildingClick(building);
          });
        }
      }
    }
  };

  // Include selectedKeys size in memo so GeoJSON re-renders on selection changes
  const selectedKeysSize = selectedKeys?.size ?? 0;
  const geoJsonData = useMemo(() => ({
    type: 'FeatureCollection' as const,
    features: buildings.map((b, i) => ({
      type: 'Feature' as const,
      id: i,
      properties: {
        area_m2: b.area_m2,
        distance_km: b.distance_km,
        lat: b.lat,
        lon: b.lon,
        solar: b.solar,
        isCustom: b.isCustom || false,
        glare_risk: b.glare_risk,
      },
      geometry: b.geometry,
    })),
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }), [buildings, selectedKeysSize]);

  const handleDrawComplete = useCallback((directPoints?: L.LatLng[]) => {
    const pts = directPoints || drawPoints;
    if (pts.length >= 3 && onDrawComplete) {
      onDrawComplete(pts.map(p => ({ lat: p.lat, lng: p.lng })));
    }
    setDrawPoints([]);
    setDrawMode('none');
  }, [drawPoints, onDrawComplete]);

  const handleDrawCompleteWith = useCallback((pts: L.LatLng[]) => {
    handleDrawComplete(pts);
  }, [handleDrawComplete]);

  const handleDrawCancel = useCallback(() => {
    setDrawPoints([]);
    setDrawMode('none');
  }, []);

  const isDrawing = drawMode !== 'none';

  return (
    <div className="relative">
      {/* Drawing Toolbar */}
      <div className="absolute top-3 right-3 z-[1000] flex flex-col gap-1.5">
        {!isDrawing ? (
          onDrawComplete && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-1.5 flex flex-col gap-1">
              <button
                onClick={() => setDrawMode('polygon')}
                className="flex items-center gap-2 px-3 py-2 text-xs font-medium text-gray-700 dark:text-gray-300 hover:bg-primary-50 dark:hover:bg-primary-900/30 hover:text-primary-700 dark:hover:text-primary-300 rounded-md transition-colors"
                title="Draw freeform polygon"
              >
                <Pencil className="w-3.5 h-3.5" />
                Draw Shape
              </button>
              <button
                onClick={() => setDrawMode('rectangle')}
                className="flex items-center gap-2 px-3 py-2 text-xs font-medium text-gray-700 dark:text-gray-300 hover:bg-primary-50 dark:hover:bg-primary-900/30 hover:text-primary-700 dark:hover:text-primary-300 rounded-md transition-colors"
                title="Click two corners to draw rectangle"
              >
                <Square className="w-3.5 h-3.5" />
                Draw Rectangle
              </button>
            </div>
          )
        ) : (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-3 min-w-[180px]">
            <div className="text-xs font-semibold text-gray-900 dark:text-gray-100 mb-2 flex items-center gap-1.5">
              <Plus className="w-3.5 h-3.5 text-primary-600" />
              {drawMode === 'polygon' ? 'Draw Polygon' : 'Draw Rectangle'}
            </div>
            <p className="text-[10px] text-gray-500 dark:text-gray-400 mb-2 leading-tight">
              {drawMode === 'polygon'
                ? 'Click to place points. Press Enter or click \u2713 when done.'
                : 'Click two opposite corners.'}
            </p>
            {drawMode === 'polygon' && (
              <div className="text-[10px] text-gray-500 dark:text-gray-400 mb-2">
                {drawPoints.length} point{drawPoints.length !== 1 ? 's' : ''} placed
              </div>
            )}
            <div className="flex gap-1.5">
              {drawMode === 'polygon' && (
                <button
                  onClick={() => handleDrawComplete()}
                  disabled={drawPoints.length < 3}
                  className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 text-xs font-medium bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                >
                  <Check className="w-3 h-3" />
                  Done
                </button>
              )}
              <button
                onClick={handleDrawCancel}
                className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              >
                <X className="w-3 h-3" />
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Drawing mode overlay indicator */}
      {isDrawing && (
        <div className="absolute top-3 left-1/2 -translate-x-1/2 z-[1000] bg-primary-600 text-white text-xs font-medium px-3 py-1.5 rounded-full shadow-lg">
          {drawMode === 'polygon' ? '🖊 Drawing polygon — click to add points' : '▭ Click first corner'}
        </div>
      )}

      <MapContainer
        center={center}
        zoom={14}
        style={{ height: '500px', width: '100%', borderRadius: '12px', cursor: isDrawing ? 'crosshair' : '' }}
        scrollWheelZoom={true}
        renderer={renderer}
      >
        <MapBoundsUpdater center={center} buildings={buildings} />
        <FlyToBuilding building={focusBuilding} />
        
        {/* Drawing handler */}
        {isDrawing && (
          <DrawingHandler
            mode={drawMode}
            points={drawPoints}
            setPoints={setDrawPoints}
            onComplete={handleDrawComplete}
            onCompleteWith={handleDrawCompleteWith}
            onCancel={handleDrawCancel}
          />
        )}
        
        {/* Satellite imagery */}
        <TileLayer
          attribution='Esri'
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        />
        
        {/* Labels overlay */}
        <TileLayer
          attribution='Esri'
          url="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"
        />
        
        {/* Buildings */}
        <GeoJSON
          key={`${airportCode}-${buildings.length}-${selectedKeysSize}`}
          data={geoJsonData}
          style={styleFeature}
          onEachFeature={onEachFeature}
        />
        
        {/* Search radius circle — non-interactive so it doesn't capture building clicks */}
        <Circle
          center={center}
          radius={radiusKm * 1000}
          interactive={false}
          pathOptions={{
            color: '#ffffff',
            weight: 2,
            opacity: 0.7,
            fillColor: 'transparent',
            fillOpacity: 0,
            dashArray: '8, 6',
          }}
        />

        {/* Airport marker */}
        <Marker position={center} icon={airportIcon}>
          <Popup>
            <strong>{airportCode}</strong> — {radiusKm} km radius
          </Popup>
        </Marker>
      </MapContainer>
    </div>
  );
}

export default memo(BuildingMapComponent);
