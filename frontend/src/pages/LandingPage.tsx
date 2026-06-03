import { Link } from 'react-router-dom';
import { Bus, Map, Zap, Leaf, ShieldCheck, BarChart3 } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="bg-white">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-emerald-50 to-white pt-24 pb-32">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10 text-center">
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-slate-900 mb-8">
            El futuro de la <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-500 to-sky-500">Movilidad Urbana</span>
          </h1>
          <p className="mx-auto max-w-2xl text-xl text-slate-600 mb-10 leading-relaxed">
            Plataforma Inteligente de Movilidad Urbana de UrbanFlow Technologies. 
            Integramos buses, metro, ciclovías, scooters y carpooling para que planifiques tu viaje reduciendo un 30% las emisiones de CO₂.
          </p>
          <div className="flex justify-center gap-4">
            <Link to="/dashboard" className="px-8 py-4 bg-emerald-500 text-white rounded-full font-semibold hover:bg-emerald-600 transition-colors shadow-lg shadow-emerald-200">
              Ir al Planificador de Rutas
            </Link>
            <a href="#solucion" className="px-8 py-4 bg-white text-slate-700 border border-slate-200 rounded-full font-semibold hover:bg-slate-50 transition-colors">
              Conoce Más
            </a>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="solucion" className="py-24 bg-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900">La solución definitiva para metrópolis</h2>
            <p className="mt-4 text-lg text-slate-600">Resolvemos la congestión vial integrando a todos los actores del ecosistema.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-12">
            <FeatureCard 
              icon={<Map className="w-8 h-8 text-emerald-500" />}
              title="Rutas Multimodales"
              description="Algoritmo basado en grafos (Neo4j) que optimiza viajes conectando buses, metro y micromovilidad."
            />
            <FeatureCard 
              icon={<Bus className="w-8 h-8 text-sky-500" />}
              title="Telemetría en Tiempo Real"
              description="Seguimiento GPS de la flota procesado con TimescaleDB y Kafka para ETA de alta precisión."
            />
            <FeatureCard 
              icon={<Leaf className="w-8 h-8 text-emerald-500" />}
              title="Impacto Ambiental"
              description="Nuestra meta: reducir 30% las emisiones de CO₂ en tres años promoviendo medios sostenibles."
            />
          </div>
        </div>
      </section>

      {/* Stakeholders Section */}
      <section className="py-24 bg-slate-50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900">Diseñado para toda la ciudad</h2>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            <StakeholderCard title="3.2M+ Ciudadanos" desc="Planifican viajes más rápidos y ecológicos." icon={<Zap />} />
            <StakeholderCard title="4.5K Conductores" desc="Optimización de rutas y tiempos." icon={<ShieldCheck />} />
            <StakeholderCard title="Centro de Control" desc="Monitoreo 24/7 y semáforos inteligentes." icon={<BarChart3 />} />
            <StakeholderCard title="Micro-movilidad" desc="Integración de scooters y bicis compartidas." icon={<Bus />} />
          </div>
        </div>
      </section>
    </div>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) {
  return (
    <div className="p-8 rounded-2xl bg-white border border-slate-100 shadow-sm hover:shadow-md transition-shadow">
      <div className="w-16 h-16 rounded-xl bg-emerald-50 flex items-center justify-center mb-6">
        {icon}
      </div>
      <h3 className="text-xl font-bold text-slate-900 mb-3">{title}</h3>
      <p className="text-slate-600 leading-relaxed">{description}</p>
    </div>
  );
}

function StakeholderCard({ title, desc, icon }: { title: string, desc: string, icon: React.ReactNode }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 flex flex-col items-center text-center">
      <div className="w-12 h-12 bg-sky-50 text-sky-500 rounded-full flex items-center justify-center mb-4">
        {icon}
      </div>
      <h4 className="font-bold text-slate-900">{title}</h4>
      <p className="text-sm text-slate-500 mt-2">{desc}</p>
    </div>
  );
}