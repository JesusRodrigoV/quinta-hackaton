import { useState, useEffect } from 'react';
import { MapPin, Search, Navigation2, Clock, DollarSign, Leaf } from 'lucide-react';
import axios from 'axios';

// Mock types basados en el backend (routing-service/app/schemas/responses.py)
interface StationInfo {
  station_id: string;
  name: string;
  type: string;
}

interface Segment {
  from_station: StationInfo;
  to_station: StationInfo;
  transport_mode: string;
  travel_time_min: number;
  distance_km: number;
}

interface RouteOption {
  total_time_min: number;
  total_cost: number;
  total_co2_kg: number;
  segments: Segment[];
}

export default function Dashboard() {
  const [stops, setStops] = useState<StationInfo[]>([]);
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [routes, setRoutes] = useState<RouteOption[]>([]);
  const [loading, setLoading] = useState(false);

  // Mock initial data fetch (Normally this would hit /api/v1/stops)
  useEffect(() => {
    // Simulating API call to routing-service
    setStops([
      { station_id: 'S1', name: 'Estación Central (Metro)', type: 'metro' },
      { station_id: 'S2', name: 'Plaza de Armas (Bus)', type: 'bus' },
      { station_id: 'S3', name: 'Parque Kennedy (Scooter)', type: 'scooter' },
      { station_id: 'S4', name: 'Campus Universitario (Bus)', type: 'bus' },
    ]);
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!origin || !destination) return;
    
    setLoading(true);
    // Simulating API call to routing-service POST /api/v1/routes
    setTimeout(() => {
      setRoutes([
        {
          total_time_min: 24,
          total_cost: 1.5,
          total_co2_kg: 0.2,
          segments: [
            {
              from_station: stops.find(s => s.station_id === origin) || stops[0],
              to_station: stops[2],
              transport_mode: 'bus',
              travel_time_min: 15,
              distance_km: 4.5
            },
            {
              from_station: stops[2],
              to_station: stops.find(s => s.station_id === destination) || stops[3],
              transport_mode: 'scooter',
              travel_time_min: 9,
              distance_km: 2.1
            }
          ]
        },
        {
          total_time_min: 35,
          total_cost: 0.8,
          total_co2_kg: 0.8,
          segments: [
            {
              from_station: stops.find(s => s.station_id === origin) || stops[0],
              to_station: stops.find(s => s.station_id === destination) || stops[3],
              transport_mode: 'bus',
              travel_time_min: 35,
              distance_km: 6.6
            }
          ]
        }
      ]);
      setLoading(false);
    }, 1000);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col lg:flex-row gap-8">
      {/* Panel Izquierdo: Buscador */}
      <div className="w-full lg:w-1/3 bg-white p-6 rounded-2xl shadow-sm border border-slate-200 h-fit">
        <h2 className="text-2xl font-bold text-slate-800 mb-6 flex items-center gap-2">
          <Search className="w-6 h-6 text-emerald-500" />
          Planificador
        </h2>
        
        <form onSubmit={handleSearch} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Origen</label>
            <div className="relative">
              <MapPin className="absolute left-3 top-3 w-5 h-5 text-slate-400" />
              <select 
                className="w-full pl-10 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-none appearance-none"
                value={origin}
                onChange={e => setOrigin(e.target.value)}
              >
                <option value="">Selecciona inicio...</option>
                {stops.map(s => <option key={s.station_id} value={s.station_id}>{s.name}</option>)}
              </select>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Destino</label>
            <div className="relative">
              <Navigation2 className="absolute left-3 top-3 w-5 h-5 text-sky-400" />
              <select 
                className="w-full pl-10 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-none appearance-none"
                value={destination}
                onChange={e => setDestination(e.target.value)}
              >
                <option value="">Selecciona destino...</option>
                {stops.map(s => <option key={s.station_id} value={s.station_id}>{s.name}</option>)}
              </select>
            </div>
          </div>

          <button 
            type="submit" 
            disabled={loading || !origin || !destination}
            className="w-full mt-4 bg-slate-900 text-white py-3 rounded-xl font-semibold hover:bg-slate-800 transition-colors disabled:opacity-50"
          >
            {loading ? 'Calculando rutas...' : 'Buscar Ruta Óptima'}
          </button>
        </form>
      </div>

      {/* Panel Derecho: Resultados y Mapa Dummy */}
      <div className="w-full lg:w-2/3 flex flex-col gap-6">
        {/* Mapa Mockup (Telemetría / Visualización) */}
        <div className="w-full h-64 bg-slate-200 rounded-2xl flex items-center justify-center relative overflow-hidden border border-slate-300">
          <div className="absolute inset-0 opacity-20 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-slate-400 to-transparent background-grid"></div>
          <div className="z-10 flex flex-col items-center">
            <Map className="w-12 h-12 text-slate-400 mb-2" />
            <p className="text-slate-500 font-medium">Visualización de Telemetría (Kafka + TimescaleDB)</p>
            <p className="text-xs text-slate-400">El mapa interactivo se renderizará aquí</p>
          </div>
          {/* Un par de puntos de vehículos */}
          <div className="absolute top-1/4 left-1/4 w-3 h-3 bg-sky-500 rounded-full animate-ping"></div>
          <div className="absolute bottom-1/3 right-1/3 w-3 h-3 bg-emerald-500 rounded-full animate-ping"></div>
        </div>

        {/* Opciones de Rutas */}
        {routes.length > 0 && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-800">Opciones recomendadas</h3>
            {routes.map((route, i) => (
              <div key={i} className={`p-5 rounded-2xl border ${i === 0 ? 'border-emerald-500 bg-emerald-50/30' : 'border-slate-200 bg-white'}`}>
                {i === 0 && <span className="inline-block px-3 py-1 bg-emerald-100 text-emerald-700 text-xs font-bold rounded-full mb-3">Más ecológica / Rápida</span>}
                <div className="flex flex-wrap gap-6 mb-4">
                  <div className="flex items-center gap-2">
                    <Clock className="w-5 h-5 text-slate-400" />
                    <span className="font-semibold">{route.total_time_min} min</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <DollarSign className="w-5 h-5 text-slate-400" />
                    <span className="font-semibold">${route.total_cost.toFixed(2)}</span>
                  </div>
                  <div className="flex items-center gap-2 text-emerald-600">
                    <Leaf className="w-5 h-5" />
                    <span className="font-semibold">{route.total_co2_kg.toFixed(2)} kg CO₂</span>
                  </div>
                </div>
                
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  {route.segments.map((seg, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <span className="px-2 py-1 bg-slate-100 rounded-md capitalize font-medium">{seg.transport_mode}</span>
                      {idx < route.segments.length - 1 && <span>→</span>}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}