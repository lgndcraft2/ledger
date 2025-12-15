import { useState, useEffect } from 'react';
import axios from 'axios';
import { Home, ListFilter, Wallet, Sparkles, Plus, TrendingUp, TrendingDown, LogOut, Loader2 } from 'lucide-react';
import { AddTransactionModal } from './AddTransactionModal';
import { motion, AnimatePresence } from 'framer-motion';

const API_URL = 'https://ledger-tau-two.vercel.app/api';

export function Dashboard({ token, onLogout }: { token: string; onLogout: () => void }) {
  const [activeTab, setActiveTab] = useState<'home' | 'transactions' | 'debts'>('home');
  const [showModal, setShowModal] = useState(false);
  const [data, setData] = useState<any>({ stats: { total_sales: 0, active_debts: 0 }, transactions: [] });
  const [loading, setLoading] = useState(true);
  const [aiSummary, setAiSummary] = useState<string | null>(null);
  const [generatingAi, setGeneratingAi] = useState(false);

  // Filter State
  const [filterType, setFilterType] = useState<'ALL' | 'SALE' | 'PURCHASE'>('ALL');

  const fetchData = async () => {
    try {
      const res = await axios.get(`${API_URL}/dashboard`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setData(res.data);
    } catch (error) {
      console.error("Failed to fetch data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [token]);

  const generateSummary = async () => {
    setGeneratingAi(true);
    // Simulation since we don't have a direct GET endpoint for just summary in the snippet provided
    // In a real app, you'd call a dedicated endpoint. 
    // For now, we simulate the "Thinking" delay.
    setTimeout(() => {
        setAiSummary(`Based on your recent activity, your sales are up by 15%. Total revenue is N${data.stats.total_sales.toLocaleString()}. 
        Recommendation: Collect the N${data.stats.active_debts.toLocaleString()} owed by debtors to boost cash flow.`);
        setGeneratingAi(false);
    }, 2500);
  };

  const filteredTransactions = data.transactions.filter((t: any) => {
    if (activeTab === 'debts') return t.balance > 0; // Show debts
    if (filterType === 'ALL') return true;
    return t.type === filterType;
  });

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <Loader2 size={48} className="animate-spin text-purple-600" />
        </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* HEADER */}
      <div className="bg-white px-6 pt-12 pb-4 sticky top-0 z-10 border-b border-gray-100 flex justify-between items-center">
        <div>
            <h2 className="text-gray-400 text-xs font-bold tracking-wider uppercase mb-1">Market CRM</h2>
            <h1 className="text-2xl font-bold text-gray-900 capitalize">{activeTab}</h1>
        </div>
        <button onClick={onLogout} className="p-2 bg-gray-100 rounded-full text-gray-500 hover:text-red-500">
            <LogOut size={18} />
        </button>
      </div>

      {/* MAIN CONTENT AREA */}
      <div className="flex-1 overflow-y-auto px-6 py-6 pb-32">
        
        {/* --- HOME TAB --- */}
        {activeTab === 'home' && (
            <div className="space-y-6">
                {/* Stats Cards */}
                <div className="grid grid-cols-2 gap-4">
                    <div className="bg-purple-600 text-white p-5 rounded-3xl shadow-lg shadow-purple-200">
                        <div className="flex items-center gap-2 mb-2 opacity-80">
                            <TrendingUp size={16} /> <span className="text-xs font-medium">Total Sales</span>
                        </div>
                        <div className="text-2xl font-bold">₦{data.stats.total_sales.toLocaleString()}</div>
                    </div>
                    <div className="bg-white text-gray-900 p-5 rounded-3xl shadow-sm border border-gray-100">
                        <div className="flex items-center gap-2 mb-2 text-red-500">
                            <TrendingDown size={16} /> <span className="text-xs font-medium">Debts Owed</span>
                        </div>
                        <div className="text-2xl font-bold">₦{data.stats.active_debts.toLocaleString()}</div>
                    </div>
                </div>

                {/* AI Section */}
                <div className="bg-gradient-to-br from-indigo-900 to-purple-900 rounded-3xl p-6 text-white shadow-xl relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-10"><Sparkles size={80} /></div>
                    <div className="relative z-10">
                        <h3 className="font-bold text-lg mb-2 flex items-center gap-2">
                            <Sparkles size={18} className="text-yellow-400" /> AI Insights
                        </h3>
                        {aiSummary ? (
                            <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-purple-100 text-sm leading-relaxed">
                                {aiSummary}
                            </motion.p>
                        ) : (
                            <div className="space-y-3">
                                <p className="text-purple-200 text-sm">Generate a smart summary of your business performance today.</p>
                                <button 
                                    onClick={generateSummary}
                                    disabled={generatingAi}
                                    className="px-4 py-2 bg-white/10 hover:bg-white/20 backdrop-blur-md rounded-xl text-xs font-bold tracking-wide transition-all border border-white/10"
                                >
                                    {generatingAi ? 'Thinking...' : 'Generate Report'}
                                </button>
                            </div>
                        )}
                    </div>
                </div>

                {/* Recent List Preview */}
                <div>
                    <h3 className="text-sm font-bold text-gray-900 mb-4">Recent Transactions</h3>
                    <TransactionList transactions={data.transactions.slice(0, 3)} />
                </div>
            </div>
        )}

        {/* --- TRANSACTIONS & DEBTS TABS --- */}
        {(activeTab === 'transactions' || activeTab === 'debts') && (
            <div className="space-y-6">
                {activeTab === 'transactions' && (
                    <div className="flex p-1 bg-gray-200/50 rounded-xl mb-6">
                        {['ALL', 'SALE', 'PURCHASE'].map((type) => (
                            <button
                                key={type}
                                onClick={() => setFilterType(type as any)}
                                className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${
                                    filterType === type ? 'bg-white text-purple-700 shadow-sm' : 'text-gray-500'
                                }`}
                            >
                                {type}
                            </button>
                        ))}
                    </div>
                )}
                <TransactionList transactions={filteredTransactions} />
            </div>
        )}

      </div>

      {/* FAB - ADD BUTTON */}
      <div className="fixed bottom-24 right-6">
        <button 
            onClick={() => setShowModal(true)}
            className="h-14 w-14 bg-gray-900 text-white rounded-full shadow-2xl shadow-purple-900/20 flex items-center justify-center hover:scale-105 active:scale-95 transition-all"
        >
            <Plus size={24} strokeWidth={3} />
        </button>
      </div>

      {/* BOTTOM NAVIGATION */}
      <div className="bg-white border-t border-gray-100 px-6 py-4 flex justify-between items-center fixed bottom-0 w-full max-w-md">
        <NavBtn icon={Home} label="Home" active={activeTab === 'home'} onClick={() => setActiveTab('home')} />
        <NavBtn icon={ListFilter} label="History" active={activeTab === 'transactions'} onClick={() => setActiveTab('transactions')} />
        <NavBtn icon={Wallet} label="Debts" active={activeTab === 'debts'} onClick={() => setActiveTab('debts')} />
      </div>

      {/* MODAL */}
      <AnimatePresence>
        {showModal && (
            <AddTransactionModal 
                token={token} 
                onClose={() => setShowModal(false)} 
                onSuccess={() => { setShowModal(false); fetchData(); }} 
            />
        )}
      </AnimatePresence>
    </div>
  );
}

// Sub-components for cleaner code
function NavBtn({ icon: Icon, label, active, onClick }: any) {
    return (
        <button onClick={onClick} className={`flex flex-col items-center gap-1 transition-colors ${active ? 'text-purple-600' : 'text-gray-400'}`}>
            <Icon size={24} strokeWidth={active ? 2.5 : 2} />
            <span className="text-[10px] font-medium">{label}</span>
        </button>
    );
}

function TransactionList({ transactions }: { transactions: any[] }) {
    if (transactions.length === 0) return <div className="text-center text-gray-400 py-10 text-sm">No transactions found</div>;

    return (
        <div className="space-y-3">
            {transactions.map((t) => (
                <div key={t.id} className="bg-white p-4 rounded-2xl shadow-sm border border-gray-50 flex justify-between items-center">
                    <div className="flex gap-4 items-center">
                        <div className={`h-10 w-10 rounded-full flex items-center justify-center ${
                            t.type === 'SALE' ? 'bg-green-100 text-green-600' : 'bg-orange-100 text-orange-600'
                        }`}>
                            {t.type === 'SALE' ? <TrendingUp size={18} /> : <TrendingDown size={18} />}
                        </div>
                        <div>
                            <h4 className="font-bold text-gray-900 text-sm">{t.item}</h4>
                            <p className="text-xs text-gray-500">{t.party} • {t.date.split(' ')[0]}</p>
                        </div>
                    </div>
                    <div className="text-right">
                        <div className="font-bold text-gray-900 text-sm">₦{t.amount.toLocaleString()}</div>
                        {t.balance > 0 && (
                            <div className="text-[10px] font-bold text-red-500 bg-red-50 px-2 py-0.5 rounded-full inline-block mt-1">
                                Owe: ₦{t.balance.toLocaleString()}
                            </div>
                        )}
                    </div>
                </div>
            ))}
        </div>
    );
}