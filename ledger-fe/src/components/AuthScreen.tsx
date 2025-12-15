import { useState } from 'react';
import axios from 'axios';
import { Smartphone, ArrowRight, Loader2 } from 'lucide-react';

interface Props {
  onLogin: (token: string) => void;
}

export function AuthScreen({ onLogin }: Props) {
  const [step, setStep] = useState(1);
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);

  const API_URL = 'http://127.0.0.1:5000/api/auth';

  const handleRequestOtp = async () => {
    setLoading(true);
    try {
      await axios.post(`${API_URL}/login`, { phone });
      setStep(2);
    } catch (e) {
      alert('Login failed. Ensure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API_URL}/verify`, { phone, code: otp });
      onLogin(res.data.token);
    } catch (e) {
      alert('Invalid code. Try 000000');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col justify-center px-8 bg-white">
      <div className="mb-10 text-center">
        <div className="w-16 h-16 bg-purple-100 rounded-2xl flex items-center justify-center mx-auto mb-6 text-purple-600">
          <Smartphone size={32} strokeWidth={2.5} />
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-gray-900 mb-2">Welcome Back</h1>
        <p className="text-gray-500">Manage your market sales with AI.</p>
      </div>

      <div className="space-y-6">
        {step === 1 ? (
          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-gray-700 ml-1">Phone Number</label>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="0907 430 4369"
                className="w-full px-4 py-4 bg-gray-50 rounded-2xl border-none focus:ring-2 focus:ring-purple-500 outline-none transition-all text-lg"
              />
            </div>
            <button
              onClick={handleRequestOtp}
              disabled={loading || phone.length < 10}
              className="w-full py-4 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-2xl shadow-lg shadow-purple-200 disabled:opacity-50 disabled:shadow-none transition-all flex items-center justify-center gap-2"
            >
              {loading ? <Loader2 className="animate-spin" /> : <>Continue <ArrowRight size={20} /></>}
            </button>
          </div>
        ) : (
          <div className="space-y-4 animate-in fade-in slide-in-from-right-8">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-gray-700 ml-1">Enter Verification Code</label>
              <input
                type="text"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                placeholder="0 0 0 0 0 0"
                className="w-full px-4 py-4 bg-gray-50 rounded-2xl border-none focus:ring-2 focus:ring-purple-500 outline-none transition-all text-center text-2xl tracking-widest"
                maxLength={6}
              />
              <p className="text-xs text-center text-gray-400">Use 000000 for testing</p>
            </div>
            <button
              onClick={handleVerify}
              disabled={loading || otp.length < 6}
              className="w-full py-4 bg-purple-600 text-white font-bold rounded-2xl shadow-lg shadow-purple-200 flex items-center justify-center gap-2"
            >
              {loading ? <Loader2 className="animate-spin" /> : 'Verify & Login'}
            </button>
            <button onClick={() => setStep(1)} className="w-full text-sm text-gray-500 font-medium">
              Wrong number? Go back
            </button>
          </div>
        )}
      </div>
    </div>
  );
}