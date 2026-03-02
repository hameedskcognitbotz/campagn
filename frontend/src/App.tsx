import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  Users,
  Send,
  Settings,
  MessageSquare,
  Plus,
  Upload,
  TrendingUp,
  Tag,
  RefreshCw
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

// --- COMPONENTS ---

const StatCard = ({ title, value, icon: Icon, color }: any) => (
  <motion.div
    whileHover={{ y: -5 }}
    className="card"
    style={{ borderLeft: `4px solid ${color}` }}
  >
    <div className="flex items-center justify-between" style={{ display: 'flex', justifyContent: 'space-between' }}>
      <div>
        <p style={{ color: 'var(--text-dim)', fontSize: '0.875rem', marginBottom: '0.5rem' }}>{title}</p>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{value}</h2>
      </div>
      <div style={{ backgroundColor: `${color}20`, padding: '0.75rem', borderRadius: '0.5rem' }}>
        <Icon size={24} color={color} />
      </div>
    </div>
  </motion.div>
);

const Sidebar = ({ activeTab, setActiveTab }: any) => (
  <aside className="sidebar">
    <div style={{ marginBottom: '2.5rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold', background: 'linear-gradient(to right, #8b5cf6, #3b82f6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', letterSpacing: '0.1em' }}>COZHAVEN</h1>
      <p style={{ fontSize: '0.65rem', color: 'var(--text-dim)', letterSpacing: '0.2em' }}>CAMPAIGN PLATFORM</p>
    </div>
    <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      {[
        { id: 'overview', icon: BarChart3, label: 'Overview' },
        { id: 'leads', icon: Users, label: 'Leads' },
        { id: 'products', icon: Tag, label: 'Product Lab' },
        { id: 'campaigns', icon: Send, label: 'Campaigns' },
        { id: 'messages', icon: MessageSquare, label: 'Messages' },
        { id: 'settings', icon: Settings, label: 'Settings' },
      ].map((item) => (
        <button
          key={item.id}
          onClick={() => setActiveTab(item.id)}
          className={`nav-link ${activeTab === item.id ? 'active' : ''}`}
          style={{ background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left', width: '100%' }}
        >
          <item.icon size={20} />
          {item.label}
        </button>
      ))}
    </nav>
  </aside>
);

// --- TABS ---

const Overview = ({ stats }: any) => (
  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="main-content">
    <div className="header">
      <h2 style={{ fontSize: '1.875rem' }}>Business Intelligence</h2>
      <div style={{ display: 'flex', gap: '1rem' }}>
        <button onClick={() => window.location.reload()} className="badge badge-success" style={{ border: 'none', cursor: 'pointer' }}>Live Status</button>
      </div>
    </div>
    <div className="stat-grid">
      <StatCard title="Target Leads" value={stats.total_leads || 0} icon={Users} color="#8b5cf6" />
      <StatCard title="Product Library" value={stats.total_products || 0} icon={Tag} color="#10b981" />
      <StatCard title="Campaign Delivery" value={stats.messages_sent || 0} icon={Send} color="#3b82f6" />
      <StatCard title="AI Intent Rate" value={`${(stats.reply_rate || 0).toFixed(1)}%`} icon={TrendingUp} color="#f59e0b" />
    </div>

    <div style={{ padding: '2rem' }}>
      <div className="card">
        <h3 style={{ marginBottom: '1rem' }}>Intent Breakdown</h3>
        <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
          {Object.entries(stats.intents || {}).map(([intent, count]: any) => (
            <div key={intent} className="card" style={{ padding: '1rem', flex: '1', minWidth: '150px' }}>
              <p style={{ textTransform: 'capitalize', color: 'var(--text-dim)' }}>{intent}</p>
              <h4 style={{ fontSize: '1.25rem' }}>{count}</h4>
            </div>
          ))}
        </div>
      </div>
    </div>
  </motion.div>
);

const Leads = () => {
  const [leads, setLeads] = useState([]);
  const [uploading, setUploading] = useState(false);

  const fetchLeads = async () => {
    try {
      const res = await api.get('/leads');
      setLeads(res.data);
    } catch (e) {
      console.error("Failed to fetch leads", e);
    }
  };

  useEffect(() => { fetchLeads(); }, []);

  const handleFileUpload = async (e: any) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    setUploading(true);
    try {
      await api.post('/leads/import', formData);
      await fetchLeads();
    } catch (e) {
      alert("Import failed. Check CSV format.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="main-content">
      <div className="header">
        <h2 style={{ fontSize: '1.875rem' }}>Lead Management</h2>
        <label className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
          <Upload size={18} />
          {uploading ? 'Processing...' : 'Import CSV'}
          <input type="file" onChange={handleFileUpload} style={{ display: 'none' }} accept=".csv" />
        </label>
      </div>
      <div className="table-container">
        <table className="card" style={{ width: '100%', borderCollapse: 'separate', borderSpacing: '0 8px' }}>
          <thead>
            <tr>
              <th>Name</th>
              <th>Phone</th>
              <th>Area</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {leads.length === 0 && (
              <tr><td colSpan={4} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-dim)' }}>No leads found. Import a CSV to get started.</td></tr>
            )}
            {leads.map((lead: any) => (
              <tr key={lead.id} style={{ background: 'var(--glass)', borderRadius: '0.5rem' }}>
                <td style={{ padding: '1rem', borderTopLeftRadius: '0.5rem', borderBottomLeftRadius: '0.5rem' }}>{lead.first_name}</td>
                <td style={{ padding: '1rem' }}>{lead.phone_number}</td>
                <td style={{ padding: '1rem' }}>{lead.area || 'Mississauga'}</td>
                <td style={{ padding: '1rem', borderTopRightRadius: '0.5rem', borderBottomRightRadius: '0.5rem' }}>
                  <span className="badge badge-success">Subscribed</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </motion.div>
  );
};

const Campaigns = () => {
  const [campaigns, setCampaigns] = useState([]);
  const [showNew, setShowNew] = useState(false);
  const [name, setName] = useState('Spring Sale Launch');
  const [template, setTemplate] = useState('Hi {{FirstName}}, our Spring Sale starts today! Financing available. Visit us for 50% off sofas! Store: 123 Budget St.');

  const fetchCampaigns = async () => {
    try {
      const res = await api.get('/campaigns');
      setCampaigns(res.data);
    } catch (e) { console.error(e); }
  };

  useEffect(() => { fetchCampaigns(); }, []);

  const createCampaign = async () => {
    try {
      await api.post('/campaigns', { name, template, status: 'scheduled' });
      setShowNew(false);
      fetchCampaigns();
    } catch (e) { alert("Failed to create campaign"); }
  };

  const triggerSend = async (id: number) => {
    try {
      await api.post(`/campaigns/${id}/send`);
      fetchCampaigns();
      alert("Campaign sequence triggered!");
    } catch (e) { alert("Failed to trigger campaign"); }
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="main-content">
      <div className="header">
        <h2 style={{ fontSize: '1.875rem' }}>Campaigns</h2>
        <button onClick={() => setShowNew(true)} className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Plus size={18} /> New Campaign
        </button>
      </div>

      <div style={{ padding: '0 2rem' }}>
        {showNew && (
          <div className="card" style={{ marginBottom: '2rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <h3>Create Sequence</h3>
            <input
              value={name} onChange={e => setName(e.target.value)}
              placeholder="Campaign Name"
              style={{ padding: '0.75rem', background: '#00000040', border: '1px solid var(--glass-border)', color: 'white', borderRadius: '0.5rem' }}
            />
            <textarea
              value={template} onChange={e => setTemplate(e.target.value)}
              placeholder="SMS Template (use {{FirstName}})"
              rows={4}
              style={{ padding: '0.75rem', background: '#00000040', border: '1px solid var(--glass-border)', color: 'white', borderRadius: '0.5rem' }}
            />
            <div style={{ display: 'flex', gap: '1rem' }}>
              <button onClick={createCampaign} className="btn-primary">Save Campaign</button>
              <button onClick={() => setShowNew(false)} style={{ background: 'none', border: '1px solid var(--glass-border)', color: 'white', padding: '0.75rem 1.5rem', borderRadius: '0.5rem' }}>Cancel</button>
            </div>
          </div>
        )}

        <div className="stat-grid" style={{ gridTemplateColumns: '1fr' }}>
          {campaigns.map((camp: any) => (
            <div key={camp.id} className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h4 style={{ fontSize: '1.125rem' }}>{camp.name}</h4>
                <p style={{ color: 'var(--text-dim)', fontSize: '0.875rem', marginTop: '0.5rem' }}>{camp.template}</p>
                <div style={{ marginTop: '0.5rem' }}>
                  <span className={`badge ${camp.status === 'active' ? 'badge-success' : 'badge-warning'}`}>{camp.status}</span>
                </div>
              </div>
              {camp.status === 'scheduled' && (
                <button onClick={() => triggerSend(camp.id)} className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Send size={16} /> Send Now
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
};

const Messages = () => {
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    const fetch = async () => {
      // In a real app we'd have a messages endpoint. 
      // For now, let's use stats or a new endpoint if we had one.
      // Let's assume we can add a /messages endpoint to main.py
      try {
        const res = await axios.get('http://localhost:8000/messages');
        setMessages(res.data);
      } catch (e) { }
    };
    fetch();
    const inv = setInterval(fetch, 5000);
    return () => clearInterval(inv);
  }, []);

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="main-content">
      <div className="header">
        <h2 style={{ fontSize: '1.875rem' }}>Live Conversations</h2>
      </div>
      <div style={{ padding: '0 2rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {messages.map((msg: any) => (
          <div key={msg.id} className="card" style={{ alignSelf: msg.direction === 'inbound' ? 'flex-start' : 'flex-end', maxWidth: '70%' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '0.25rem', display: 'flex', justifyContent: 'space-between' }}>
              <span>{msg.direction === 'inbound' ? 'Customer' : 'System'}</span>
              <span>{msg.intent && `[Intent: ${msg.intent}]`}</span>
            </div>
            <p>{msg.content}</p>
          </div>
        ))}
      </div>
    </motion.div>
  )
}

const Products = () => {
  const [products, setProducts] = useState([]);
  const [syncing, setSyncing] = useState(false);

  const fetchItems = async () => {
    try {
      const res = await api.get('/products');
      setProducts(res.data);
    } catch (e) { }
  };

  useEffect(() => { fetchItems(); }, []);

  const runSync = async () => {
    setSyncing(true);
    try {
      await api.post('/sync/products');
      await api.post('/sync/leads');
      await fetchItems();
      alert("Everything Synced! Leads and Products updated from Excel.");
    } catch (e) { alert("Sync failed"); }
    finally { setSyncing(false); }
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="main-content">
      <div className="header">
        <h2 style={{ fontSize: '1.875rem' }}>Product Lab</h2>
        <button onClick={runSync} className="badge" style={{ background: 'var(--accent)', color: 'white', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 1rem' }}>
          <RefreshCw size={14} className={syncing ? 'animate-spin' : ''} />
          {syncing ? 'Syncing Excel...' : 'Sync from Source'}
        </button>
      </div>
      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))' }}>
        {products.map((p: any) => (
          <div key={p.id} className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span className="badge">{p.category}</span>
              <span style={{ fontWeight: 'bold', color: '#10b981' }}>${p.price.toFixed(2)}</span>
            </div>
            <h4 style={{ fontSize: '1rem' }}>{p.name}</h4>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>SKU: {p.sku}</p>
            <p style={{ fontSize: '0.8rem' }}>{p.color && `Colors: ${p.color}`}</p>
            {p.link && <a href={p.link} target="_blank" style={{ fontSize: '0.75rem', color: 'var(--accent)' }}>View Photos</a>}
          </div>
        ))}
      </div>
    </motion.div>
  );
};

// --- APP ROOT ---

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [stats, setStats] = useState<any>({});

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await api.get('/stats');
        setStats(res.data);
      } catch (e) { console.error(e); }
    };
    fetchStats();
    const interval = setInterval(fetchStats, 10000); // Polling
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="dashboard-container">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <main style={{ overflowY: 'auto' }}>
        <AnimatePresence mode="wait">
          {activeTab === 'overview' && <Overview key="overview" stats={stats} />}
          {activeTab === 'leads' && <Leads key="leads" />}
          {activeTab === 'products' && <Products key="products" />}
          {activeTab === 'campaigns' && <Campaigns key="campaigns" />}
          {activeTab === 'messages' && <Messages key="messages" />}
          {activeTab === 'settings' && (
            <div className="main-content">
              <div className="header"><h2>Settings</h2></div>
              <div style={{ padding: '0 2rem' }}>
                <div className="card">
                  <p>Configuration for Twilio & AI (Locked for Security)</p>
                </div>
              </div>
            </div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
