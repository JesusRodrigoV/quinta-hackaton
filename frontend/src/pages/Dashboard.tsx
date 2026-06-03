import { useState, useEffect } from 'react';
import { 
  Search, 
  Map as MapIcon, 
  Wallet, 
  ShieldCheck, 
  Zap, 
  Clock, 
  Leaf, 
  Navigation2, 
  MapPin,
  History,
  CreditCard,
  AlertTriangle
} from 'lucide-react';
import { routingService, sharedMobilityService, paymentService, auditService } from '../services/api';

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<'planner' | 'mobility' | 'wallet' | 'audit'>('planner');
  
  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Navigation Tabs */}
        <div className="flex flex-wrap gap-2 mb-8 bg-white p-2 rounded-2xl shadow-sm border border-slate-200">
          <TabButton 
            active={activeTab === 'planner'} 
            onClick={() => setActiveTab('planner')} 
            icon={<Search className="w-4 h-4" />}
            label="Planificador"
          />
          <TabButton 
            active={activeTab === 'mobility'} 
            onClick={() => setActiveTab('mobility')} 
            icon={<Zap className="w-4 h-4" />}
            label="Movilidad Compartida"
          />
          <TabButton 
            active={activeTab === 'wallet'} 
            onClick={() => setActiveTab('wallet')} 
            icon={<Wallet className="w-4 h-4" />}
            label="Mi Billetera"
          />
          <TabButton 
            active={activeTab === 'audit'} 
            onClick={() => setActiveTab('audit')} 
            icon={<ShieldCheck className="w-4 h-4" />}
            label="Auditoría"
          />
        </div>

        {/* Content Area */}
        <div className="transition-all duration-300">
          {activeTab === 'planner' && <PlannerTab />}
          {activeTab === 'mobility' && <MobilityTab />}
          {activeTab === 'wallet' && <WalletTab />}
          {activeTab === 'audit' && <AuditTab />}
        </div>
      </div>
    </div>
  );
}

function TabButton({ active, onClick, icon, label }: any) {
  return (
    <button 
      onClick={onClick}
      className={`flex items-center gap-2 px-6 py-3 rounded-xl font-medium transition-all ${
        active 
        ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-200' 
        : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'
      }`}
    >
      {icon}
      {label}
    </button>
  );
}

// --- TAB COMPONENTS ---

function PlannerTab() {
  const [stops, setStops] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [routes, setRoutes] = useState<any[]>([]);

  useEffect(() => {
    routingService.getStops().then(res => setStops(res.data.stops)).catch(() => {
      // Fallback mocks
      setStops([
        { station_id: 'S1', name: 'Estación Central', type: 'metro' },
        { station_id: 'S2', name: 'Plaza de Armas', type: 'bus' },
      ]);
    });
  }, []);

  return (
    <div className="grid lg:grid-cols-3 gap-8">
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm h-fit">
        <h3 className="text-xl font-bold mb-6">Planifica tu viaje multimodal</h3>
        <div className="space-y-4">
          <div className="relative">
            <MapPin className="absolute left-3 top-3.5 w-5 h-5 text-slate-400" />
            <select className="w-full pl-10 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl appearance-none outline-none focus:ring-2 focus:ring-emerald-500">
              <option>Origen...</option>
              {stops.map(s => <option key={s.station_id}>{s.name}</option>)}
            </select>
          </div>
          <div className="relative">
            <Navigation2 className="absolute left-3 top-3.5 w-5 h-5 text-sky-400" />
            <select className="w-full pl-10 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl appearance-none outline-none focus:ring-2 focus:ring-emerald-500">
              <option>Destino...</option>
              {stops.map(s => <option key={s.station_id}>{s.name}</option>)}
            </select>
          </div>
          <button className="w-full py-4 bg-slate-900 text-white rounded-xl font-bold hover:bg-slate-800">Calcular Ruta Óptima</button>
        </div>
      </div>
      <div className="lg:col-span-2 space-y-4">
        <div className="h-96 bg-slate-200 rounded-2xl flex items-center justify-center border border-slate-300 relative overflow-hidden">
           <MapIcon className="w-12 h-12 text-slate-400 mb-2" />
           <p className="text-slate-500">Visualización de Grafos y Telemetría</p>
           <div className="absolute top-2 right-2 bg-white/80 backdrop-blur p-3 rounded-lg text-xs font-bold border border-slate-200">
             <div className="flex items-center gap-2"><div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div> Buses en Línea</div>
             <div className="flex items-center gap-2 mt-1"><div className="w-2 h-2 bg-sky-500 rounded-full animate-pulse"></div> Metro Activo</div>
           </div>
        </div>
      </div>
    </div>
  );
}

function MobilityTab() {
  const [vehicles, setVehicles] = useState<any[]>([]);

  useEffect(() => {
    sharedMobilityService.getVehicles().then(res => setVehicles(res.data)).catch(() => {
      setVehicles([
        { vehicle_id: 'SC-101', type: 'scooter', battery_level: 85, status: 'available' },
        { vehicle_id: 'BK-202', type: 'ebike', battery_level: 42, status: 'in_use' },
      ]);
    });
  }, []);

  return (
    <div className="grid md:grid-cols-3 gap-6">
      {vehicles.map(v => (
        <div key={v.vehicle_id} className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex justify-between items-start mb-4">
            <div className={`p-3 rounded-xl ${v.type === 'scooter' ? 'bg-orange-50 text-orange-500' : 'bg-emerald-50 text-emerald-500'}`}>
              <Zap className="w-6 h-6" />
            </div>
            <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${v.status === 'available' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>
              {v.status}
            </span>
          </div>
          <h4 className="text-lg font-bold text-slate-900">{v.type === 'scooter' ? 'Scooter Eléctrico' : 'Bicicleta Eléctrica'}</h4>
          <p className="text-sm text-slate-500 font-mono mb-4">{v.vehicle_id}</p>
          <div className="flex items-center gap-2 mb-6">
            <div className="flex-grow bg-slate-100 h-2 rounded-full overflow-hidden">
              <div className="bg-emerald-500 h-full" style={{ width: `${v.battery_level}%` }}></div>
            </div>
            <span className="text-xs font-bold text-slate-700">{v.battery_level}%</span>
          </div>
          <button className="w-full py-3 bg-emerald-500 text-white rounded-xl font-bold hover:bg-emerald-600">Reservar Ahora</button>
        </div>
      ))}
    </div>
  );
}

function WalletTab() {
  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Wallet Card */}
      <div className="bg-gradient-to-br from-slate-900 to-slate-800 p-8 rounded-3xl text-white shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 p-8 opacity-10">
          <CreditCard className="w-32 h-32" />
        </div>
        <div className="relative z-10">
          <p className="text-slate-400 font-medium mb-1">Saldo Disponible</p>
          <h2 className="text-4xl font-bold mb-8">$12,450.00</h2>
          <div className="flex gap-4">
            <button className="px-6 py-2 bg-emerald-500 rounded-full font-bold text-sm hover:bg-emerald-600 transition-colors">Recargar Saldo</button>
            <button className="px-6 py-2 bg-white/10 rounded-full font-bold text-sm hover:bg-white/20 transition-colors">Vincular NFC</button>
          </div>
        </div>
      </div>

      {/* History */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm">
        <div className="p-6 border-b border-slate-100 flex justify-between items-center">
          <h3 className="text-lg font-bold flex items-center gap-2"><History className="w-5 h-5 text-emerald-500" /> Historial Unificado</h3>
          <span className="text-xs text-slate-400">ISO 20022 Compliant</span>
        </div>
        <div className="divide-y divide-slate-50">
          {[
            { id: 1, mode: 'metro', amount: -2.5, time: 'Hace 2 horas', status: 'completed' },
            { id: 2, mode: 'scooter', amount: -4.8, time: 'Hace 5 horas', status: 'completed' },
            { id: 3, mode: 'deposit', amount: 50.0, time: 'Ayer', status: 'completed' },
          ].map(t => (
            <div key={t.id} className="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
              <div className="flex items-center gap-4">
                <div className={`p-2 rounded-lg ${t.amount < 0 ? 'bg-slate-100 text-slate-500' : 'bg-emerald-100 text-emerald-500'}`}>
                  {t.amount < 0 ? <Clock className="w-4 h-4" /> : <Zap className="w-4 h-4" />}
                </div>
                <div>
                  <p className="font-bold text-slate-800 capitalize">{t.mode}</p>
                  <p className="text-xs text-slate-400">{t.time}</p>
                </div>
              </div>
              <p className={`font-mono font-bold ${t.amount < 0 ? 'text-slate-800' : 'text-emerald-500'}`}>
                {t.amount < 0 ? '' : '+'}{t.amount.toFixed(2)}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function AuditTab() {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="p-6 bg-slate-900 text-white flex justify-between items-center">
        <div>
          <h3 className="text-lg font-bold">Libro Mayor de Auditoría Inmutable</h3>
          <p className="text-xs text-slate-400">Validación Criptográfica SHA-256 activa</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1 bg-emerald-500/20 border border-emerald-500/30 rounded-full text-emerald-400 text-xs font-bold">
          <ShieldCheck className="w-3 h-3" />
          Sistema Verificado
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead className="bg-slate-50 border-b border-slate-100">
            <tr>
              <th className="p-4 text-xs font-bold text-slate-500 uppercase">Evento ID</th>
              <th className="p-4 text-xs font-bold text-slate-500 uppercase">Servicio</th>
              <th className="p-4 text-xs font-bold text-slate-500 uppercase">Timestamp</th>
              <th className="p-4 text-xs font-bold text-slate-500 uppercase">Hash Anterior</th>
              <th className="p-4 text-xs font-bold text-slate-500 uppercase">Estado</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {[
              { id: 'ev-982', svc: 'Payment', time: '2026-06-02 14:22:01', hash: '8f3a...c21d', status: 'valid' },
              { id: 'ev-981', svc: 'Routing', time: '2026-06-02 14:21:45', hash: 'd9e1...45a0', status: 'valid' },
              { id: 'ev-980', svc: 'Telemetry', time: '2026-06-02 14:21:10', hash: 'a2f4...ee82', status: 'valid' },
            ].map(log => (
              <tr key={log.id} className="hover:bg-slate-50 text-sm">
                <td className="p-4 font-mono font-bold text-slate-700">{log.id}</td>
                <td className="p-4"><span className="px-2 py-1 bg-slate-100 rounded-md text-xs font-bold text-slate-600">{log.svc}</span></td>
                <td className="p-4 text-slate-500">{log.time}</td>
                <td className="p-4 font-mono text-xs text-slate-400">{log.hash}</td>
                <td className="p-4">
                  <div className="flex items-center gap-1 text-emerald-500 font-bold text-xs uppercase">
                    <ShieldCheck className="w-3 h-3" /> Integrado
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}