import { useState, type InputHTMLAttributes } from 'react';
import axios from 'axios';
import { X, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';

interface AddTransactionModalProps {
  token: string;
  onClose: () => void;
  onSuccess: () => void;
}

interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'onChange'> {
  label: string;
  onChange: (value: string) => void;
}

export function AddTransactionModal({ token, onClose, onSuccess }: AddTransactionModalProps) {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    type: 'SALE',
    party_name: '',
    item_name: '',
    quantity: 1,
    total_amount: '',
    amount_paid: ''
  });

  const handleSubmit = async () => {
    setLoading(true);
    try {
      await axios.post('http://127.0.0.1:5000/api/transaction/add', {
        ...formData,
        total_amount: Number(formData.total_amount),
        amount_paid: Number(formData.amount_paid || formData.total_amount) // Default to full pay
      }, { headers: { Authorization: `Bearer ${token}` }});
      onSuccess();
    } catch (e) {
      alert("Error saving transaction");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center">
        {/* Backdrop */}
        <motion.div 
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={onClose} className="absolute inset-0 bg-black/40 backdrop-blur-sm" 
        />
        
        {/* Modal Content */}
        <motion.div 
            initial={{ y: "100%" }} animate={{ y: 0 }} exit={{ y: "100%" }}
            className="bg-white w-full max-w-md rounded-t-3xl sm:rounded-3xl p-6 relative z-10 shadow-2xl"
        >
            <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold text-gray-900">New Transaction</h3>
                <button onClick={onClose} className="p-2 bg-gray-100 rounded-full text-gray-500"><X size={20}/></button>
            </div>

            <div className="space-y-4">
                {/* Type Toggle */}
                <div className="bg-gray-100 p-1 rounded-xl flex mb-4">
                    {['SALE', 'PURCHASE'].map((t) => (
                        <button
                            key={t}
                            onClick={() => setFormData({...formData, type: t})}
                            className={`flex-1 py-3 text-sm font-bold rounded-lg transition-all ${
                                formData.type === t ? 'bg-white shadow-sm text-purple-700' : 'text-gray-400'
                            }`}
                        >
                            {t}
                        </button>
                    ))}
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <Input label="Item Name" placeholder="Rice, Yam..." value={formData.item_name} onChange={v => setFormData({...formData, item_name: v})} />
                    <Input label="Quantity" type="number" value={formData.quantity} onChange={v => setFormData({...formData, quantity: Number(v)})} />
                </div>
                
                <Input label={formData.type === 'SALE' ? "Customer Name" : "Supplier Name"} placeholder="Enter name..." value={formData.party_name} onChange={v => setFormData({...formData, party_name: v})} />
                
                <div className="grid grid-cols-2 gap-4">
                    <Input label="Total Amount (₦)" type="number" placeholder="0.00" value={formData.total_amount} onChange={v => setFormData({...formData, total_amount: v})} />
                    <Input label="Amount Paid (₦)" type="number" placeholder="0.00" value={formData.amount_paid} onChange={v => setFormData({...formData, amount_paid: v})} />
                </div>

                <button 
                    onClick={handleSubmit} 
                    disabled={loading}
                    className="w-full bg-gray-900 text-white font-bold py-4 rounded-2xl mt-4 flex items-center justify-center"
                >
                    {loading ? <Loader2 className="animate-spin" /> : 'Save Transaction'}
                </button>
            </div>
        </motion.div>
    </div>
  );
}

const Input = ({ label, onChange, ...props }: InputProps) => (
    <div className="space-y-1">
        <label className="text-xs font-bold text-gray-500 uppercase tracking-wide ml-1">{label}</label>
        <input 
            className="w-full bg-gray-50 border-none rounded-xl px-4 py-3 font-medium text-gray-900 focus:ring-2 focus:ring-purple-500 outline-none transition-all"
            onChange={(e) => onChange(e.target.value)}
            {...props}
        />
    </div>
);