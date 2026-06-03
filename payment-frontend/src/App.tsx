import { useState, useEffect } from 'react'
import { Wallet, Activity, CreditCard, CheckCircle2, AlertCircle } from 'lucide-react'

function App() {
  const [status, setStatus] = useState<'loading' | 'online' | 'offline'>('loading')
  const [amount, setAmount] = useState('')
  const [message, setMessage] = useState('')

  const checkHealth = async () => {
    try {
      const res = await fetch('http://localhost:3000/health')
      if (res.ok) setStatus('online')
      else setStatus('offline')
    } catch {
      setStatus('offline')
    }
  }

  useEffect(() => {
    checkHealth()
    const interval = setInterval(checkHealth, 5000)
    return () => clearInterval(interval)
  }, [])

  const handlePayment = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const res = await fetch('http://localhost:3000/payments/initiate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: parseFloat(amount), currency: 'USD' })
      })
      const data = await res.json()
      setMessage(`Exito: ${data.message}`)
    } catch (err) {
      setMessage('Error al conectar con el servidor')
    }
  }

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif', maxWidth: '400px', margin: '0 auto' }}>
      <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h2>Payment App</h2>
        <div style={{ display: 'flex', alignItems: 'center', color: status === 'online' ? 'green' : 'red' }}>
          <Activity size={16} style={{ marginRight: '5px' }} />
          <span>{status.toUpperCase()}</span>
        </div>
      </header>

      <div style={{ background: '#f4f4f4', padding: '15px', borderRadius: '8px', marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '10px' }}>
          <Wallet style={{ marginRight: '10px' }} />
          <strong>Saldo Virtual: $100.00</strong>
        </div>
      </div>

      <form onSubmit={handlePayment} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <label>Monto a pagar:</label>
        <input 
          type="number" 
          value={amount} 
          onChange={(e) => setAmount(e.target.value)}
          placeholder="0.00"
          style={{ padding: '10px', borderRadius: '4px', border: '1px solid #ccc' }}
        />
        <button 
          type="submit" 
          style={{ 
            padding: '10px', 
            background: '#007bff', 
            color: 'white', 
            border: 'none', 
            borderRadius: '4px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          <CreditCard size={18} style={{ marginRight: '8px' }} />
          Pagar Ahora
        </button>
      </form>

      {message && (
        <div style={{ 
          marginTop: '20px', 
          padding: '10px', 
          borderRadius: '4px', 
          background: message.includes('Error') ? '#fee' : '#efe',
          display: 'flex',
          alignItems: 'center'
        }}>
          {message.includes('Error') ? <AlertCircle color="red" /> : <CheckCircle2 color="green" />}
          <span style={{ marginLeft: '10px' }}>{message}</span>
        </div>
      )}
    </div>
  )
}

export default App
