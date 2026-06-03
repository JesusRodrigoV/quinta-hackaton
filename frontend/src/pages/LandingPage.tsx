import { Link } from 'react-router-dom';
import { 
  Bus, 
  Map as MapIcon, 
  Zap, 
  Leaf, 
  ShieldCheck, 
  BarChart3, 
  Globe, 
  CreditCard, 
  Smartphone,
  CheckCircle2
} from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="bg-white">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-emerald-50 to-white pt-24 pb-32">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-100 text-emerald-700 text-sm font-bold mb-8">
              <Globe className="w-4 h-4" />
              Impacto CO₂: Meta -30% en 3 años
            </div>
            <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-slate-900 mb-8 leading-tight">
              Reinventando la <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-500 to-sky-500">Movilidad Urbana</span>
            </h1>
            <p className="mx-auto max-w-3xl text-xl text-slate-600 mb-12 leading-relaxed">
              UrbanFlow Technologies Ltda. despliega la plataforma más avanzada de integración multimodal. 
              Buses, Metro, Scooters, Bicis y Carpooling en una sola interfaz inteligente.
            </p>
            <div className="flex flex-col sm:flex-row justify-center gap-4">
              <Link to="/dashboard" className="px-10 py-5 bg-emerald-500 text-white rounded-2xl font-bold hover:bg-emerald-600 transition-all shadow-xl shadow-emerald-200 flex items-center justify-center gap-2">
                <Smartphone className="w-5 h-5" />
                Explorar App Ciudadana
              </Link>
              <a href="#arquitectura" className="px-10 py-5 bg-slate-900 text-white rounded-2xl font-bold hover:bg-slate-800 transition-all flex items-center justify-center gap-2">
                <BarChart3 className="w-5 h-5" />
                Panel de Autoridades
              </a>
            </div>
          </div>
        </div>
        
        {/* Animated City Background Element */}
        <div className="absolute bottom-0 left-0 right-0 h-32 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-5"></div>
      </section>

      {/* Stats Section */}
      <section className="py-20 bg-slate-900 text-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-4xl font-bold text-emerald-400 mb-2">5M+</div>
              <div className="text-slate-400 text-sm">Habitantes Impactados</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-emerald-400 mb-2">3.2M</div>
              <div className="text-slate-400 text-sm">Usuarios Activos</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-emerald-400 mb-2">4,500</div>
              <div className="text-slate-400 text-sm">Buses Conectados</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-emerald-400 mb-2">30%</div>
              <div className="text-slate-400 text-sm">Reducción CO₂ Proyectada</div>
            </div>
          </div>
        </div>
      </section>

      {/* Services/Microservices Integration Section */}
      <section id="arquitectura" className="py-24 bg-white overflow-hidden">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="lg:flex items-center gap-16">
            <div className="lg:w-1/2 mb-12 lg:mb-0">
              <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-6">Un ecosistema de Microservicios para una Ciudad Inteligente</h2>
              <p className="text-lg text-slate-600 mb-8">Nuestra arquitectura desacoplada garantiza escalabilidad masiva y fiabilidad del 99.99%.</p>
              
              <div className="space-y-6">
                <IntegrationItem 
                  icon={<MapIcon className="text-emerald-500" />} 
                  title="Planificación Multimodal (Neo4j)" 
                  desc="Cálculo de rutas óptimas cruzando todos los medios de transporte en milisegundos."
                />
                <IntegrationItem 
                  icon={<Zap className="text-sky-500" />} 
                  title="Telemetría Real-Time (Kafka + Timescale)" 
                  desc="Seguimiento GPS de alta frecuencia para ETAs dinámicos y precisos."
                />
                <IntegrationItem 
                  icon={<CreditCard className="text-purple-500" />} 
                  title="Pagos Unificados (ISO 20022)" 
                  desc="Sistema de pago transaccional ACID para buses, metro y scooters."
                />
                <IntegrationItem 
                  icon={<ShieldCheck className="text-emerald-500" />} 
                  title="Auditoría Inmutable (Hashing)" 
                  desc="Transparencia total para autoridades municipales con logs verificables."
                />
              </div>
            </div>
            <div className="lg:w-1/2 relative">
              <div className="relative z-10 bg-slate-100 rounded-3xl p-4 shadow-2xl border border-slate-200">
                <img 
                  src="https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?q=80&w=2069&auto=format&fit=crop" 
                  alt="City Traffic Management" 
                  className="rounded-2xl shadow-inner h-[500px] w-full object-cover"
                />
                <div className="absolute -bottom-6 -left-6 bg-white p-6 rounded-2xl shadow-xl border border-slate-100 max-w-xs">
                  <div className="flex items-center gap-3 mb-2">
                    <CheckCircle2 className="text-emerald-500 w-5 h-5" />
                    <span className="font-bold text-slate-800 text-sm">Semáforos Inteligentes</span>
                  </div>
                  <p className="text-xs text-slate-500 leading-relaxed">Prioridad de paso para transporte público basada en telemetría NTCIP.</p>
                </div>
              </div>
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120%] h-[120%] bg-emerald-100 rounded-full blur-3xl opacity-20 -z-10"></div>
            </div>
          </div>
        </div>
      </section>

      {/* Stakeholders CTA */}
      <section className="py-24 bg-slate-50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-slate-900 mb-12">Soluciones para cada actor de la movilidad</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <RoleCard 
              title="Ciudadanos" 
              desc="App móvil para planificar rutas, pagar con QR/NFC y reservar scooters." 
              points={['Rutas Eco-Friendly', 'Pago Unificado', 'Alertas Real-Time']}
            />
            <RoleCard 
              title="Operadores" 
              desc="Centro de Control para monitoreo de flota y gestión de incidencias 24/7." 
              points={['Mapa de Telemetría', 'Gestión de Alertas', 'Optimización de Carga']}
            />
            <RoleCard 
              title="Autoridades" 
              desc="Portal de BI y Planificación Urbana con datos auditables e inmutables." 
              points={['Reportes de Emisiones', 'Libro de Auditoría', 'Predicción de Congestión']}
            />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-100 py-12">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-emerald-500 rounded-lg flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-slate-900">UrbanFlow Technologies Ltda.</span>
          </div>
          <p className="text-sm text-slate-400">© 2026 Movilidad Inteligente para Metrópolis.</p>
        </div>
      </footer>
    </div>
  );
}

function IntegrationItem({ icon, title, desc }: any) {
  return (
    <div className="flex gap-4">
      <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-white border border-slate-100 shadow-sm flex items-center justify-center">
        {icon}
      </div>
      <div>
        <h4 className="font-bold text-slate-800 mb-1">{title}</h4>
        <p className="text-sm text-slate-500 leading-relaxed">{desc}</p>
      </div>
    </div>
  );
}

function RoleCard({ title, desc, points }: any) {
  return (
    <div className="bg-white p-8 rounded-3xl border border-slate-100 shadow-sm text-left hover:shadow-md transition-shadow">
      <h3 className="text-xl font-bold text-slate-900 mb-4">{title}</h3>
      <p className="text-slate-500 text-sm mb-6 leading-relaxed">{desc}</p>
      <ul className="space-y-3">
        {points.map((p: string) => (
          <li key={p} className="flex items-center gap-2 text-sm font-medium text-slate-700">
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            {p}
          </li>
        ))}
      </ul>
    </div>
  );
}