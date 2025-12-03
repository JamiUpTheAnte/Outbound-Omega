/**
 * Outbound Omega v2 - React Frontend
 * Galaxy-themed UI for lead management and outbound automation
 */

const { useState, useEffect } = React;

// =============================================================================
// API Service
// =============================================================================

const API = {
    baseURL: '/api',

    async get(endpoint) {
        const response = await fetch(`${this.baseURL}${endpoint}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
    },

    async post(endpoint, data) {
        const response = await fetch(`${this.baseURL}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
    },

    async put(endpoint, data) {
        const response = await fetch(`${this.baseURL}${endpoint}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
    }
};

// =============================================================================
// Main App Component
// =============================================================================

function App() {
    const [currentView, setCurrentView] = useState('dashboard');
    const [stats, setStats] = useState(null);

    useEffect(() => {
        loadStats();
    }, []);

    const loadStats = async () => {
        try {
            const data = await API.get('/dashboard/stats');
            setStats(data);
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    };

    return (
        <div className="app">
            <Sidebar currentView={currentView} setCurrentView={setCurrentView} />
            <div className="main-content">
                {currentView === 'dashboard' && <Dashboard stats={stats} />}
                {currentView === 'leads' && <LeadsView />}
                {currentView === 'campaigns' && <CampaignsView />}
                {currentView === 'sequences' && <SequencesView />}
                {currentView === 'outbound' && <OutboundView />}
                {currentView === 'settings' && <SettingsView />}
            </div>
        </div>
    );
}

// =============================================================================
// Sidebar Navigation
// =============================================================================

function Sidebar({ currentView, setCurrentView }) {
    const menuItems = [
        { id: 'dashboard', icon: '📊', label: 'Dashboard' },
        { id: 'leads', icon: '👥', label: 'Leads' },
        { id: 'campaigns', icon: '🎯', label: 'Campaigns' },
        { id: 'sequences', icon: '📧', label: 'Sequences' },
        { id: 'outbound', icon: '🚀', label: 'Outbound' },
        { id: 'settings', icon: '⚙️', label: 'Settings' }
    ];

    return (
        <div className="sidebar">
            <div className="sidebar-header">
                <h1>🌌 Outbound Omega</h1>
                <p className="version">v2.0</p>
            </div>
            <nav className="sidebar-nav">
                {menuItems.map(item => (
                    <button
                        key={item.id}
                        className={`nav-item ${currentView === item.id ? 'active' : ''}`}
                        onClick={() => setCurrentView(item.id)}
                    >
                        <span className="nav-icon">{item.icon}</span>
                        <span className="nav-label">{item.label}</span>
                    </button>
                ))}
            </nav>
        </div>
    );
}

// =============================================================================
// Dashboard View
// =============================================================================

function Dashboard({ stats }) {
    if (!stats) return <div className="loading">Loading...</div>;

    return (
        <div className="view dashboard-view">
            <h1>Dashboard</h1>

            <div className="stats-grid">
                <StatCard
                    title="Total Leads"
                    value={stats.total_leads}
                    icon="👥"
                    color="#667eea"
                />
                <StatCard
                    title="Total Companies"
                    value={stats.total_companies}
                    icon="🏢"
                    color="#764ba2"
                />
                <StatCard
                    title="Emails Today"
                    value={stats.emails_sent_today}
                    icon="📧"
                    color="#f093fb"
                />
                <StatCard
                    title="Active Campaigns"
                    value={stats.active_campaigns}
                    icon="🎯"
                    color="#4facfe"
                />
            </div>

            <div className="dashboard-sections">
                <div className="section">
                    <h2>Leads by Status</h2>
                    <div className="status-breakdown">
                        {Object.entries(stats.leads_by_status).map(([status, count]) => (
                            <div key={status} className="status-item">
                                <span className="status-badge">{status}</span>
                                <span className="status-count">{count}</span>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="section">
                    <h2>Recent Activities</h2>
                    <div className="activities-list">
                        {stats.recent_activities.map(activity => (
                            <div key={activity.id} className="activity-item">
                                <span className="activity-type">{activity.type}</span>
                                <span className="activity-time">
                                    {new Date(activity.created_at).toLocaleString()}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

function StatCard({ title, value, icon, color }) {
    return (
        <div className="stat-card" style={{ borderLeftColor: color }}>
            <div className="stat-icon">{icon}</div>
            <div className="stat-content">
                <div className="stat-value">{value}</div>
                <div className="stat-title">{title}</div>
            </div>
        </div>
    );
}

// =============================================================================
// Leads View
// =============================================================================

function LeadsView() {
    const [leads, setLeads] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState({
        status: '',
        market_type: ''
    });

    useEffect(() => {
        loadLeads();
    }, [filters]);

    const loadLeads = async () => {
        setLoading(true);
        try {
            const params = new URLSearchParams();
            if (filters.status) params.append('status', filters.status);
            if (filters.market_type) params.append('market_type', filters.market_type);

            const data = await API.get(`/leads?${params}`);
            setLeads(data.leads);
        } catch (error) {
            console.error('Failed to load leads:', error);
        }
        setLoading(false);
    };

    return (
        <div className="view leads-view">
            <div className="view-header">
                <h1>Leads</h1>
                <button className="btn btn-primary" onClick={loadLeads}>Refresh</button>
            </div>

            <div className="filters">
                <select
                    value={filters.status}
                    onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                    className="filter-select"
                >
                    <option value="">All Statuses</option>
                    <option value="new">New</option>
                    <option value="queued">Queued</option>
                    <option value="contacted">Contacted</option>
                    <option value="replied">Replied</option>
                    <option value="qualified">Qualified</option>
                    <option value="won">Won</option>
                    <option value="lost">Lost</option>
                </select>
            </div>

            {loading ? (
                <div className="loading">Loading leads...</div>
            ) : (
                <div className="table-container">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Company</th>
                                <th>Contact</th>
                                <th>Email</th>
                                <th>Status</th>
                                <th>Market Type</th>
                                <th>Score</th>
                                <th>Times Contacted</th>
                            </tr>
                        </thead>
                        <tbody>
                            {leads.map(lead => (
                                <tr key={lead.id}>
                                    <td>
                                        <strong>{lead.company?.name}</strong>
                                        <br />
                                        <small>{lead.company?.location}</small>
                                    </td>
                                    <td>{lead.contact?.name || '-'}</td>
                                    <td>{lead.contact?.email}</td>
                                    <td>
                                        <span className={`badge status-${lead.status}`}>
                                            {lead.status}
                                        </span>
                                    </td>
                                    <td>{lead.company?.market_type || '-'}</td>
                                    <td>{lead.lead_score}</td>
                                    <td>{lead.times_contacted}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}

// =============================================================================
// Campaigns View
// =============================================================================

function CampaignsView() {
    const [campaigns, setCampaigns] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadCampaigns();
    }, []);

    const loadCampaigns = async () => {
        setLoading(true);
        try {
            const data = await API.get('/campaigns');
            setCampaigns(data);
        } catch (error) {
            console.error('Failed to load campaigns:', error);
        }
        setLoading(false);
    };

    return (
        <div className="view campaigns-view">
            <div className="view-header">
                <h1>Campaigns</h1>
                <button className="btn btn-primary">+ New Campaign</button>
            </div>

            {loading ? (
                <div className="loading">Loading campaigns...</div>
            ) : (
                <div className="campaigns-grid">
                    {campaigns.map(campaign => (
                        <div key={campaign.id} className="campaign-card">
                            <div className="campaign-header">
                                <h3>{campaign.name}</h3>
                                <span className={`badge ${campaign.is_active ? 'active' : 'inactive'}`}>
                                    {campaign.is_active ? 'Active' : 'Inactive'}
                                </span>
                            </div>
                            <p className="campaign-description">{campaign.description}</p>
                            <div className="campaign-meta">
                                <div><strong>Niche:</strong> {campaign.niche}</div>
                                <div><strong>Market:</strong> {campaign.market}</div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

// =============================================================================
// Sequences View
// =============================================================================

function SequencesView() {
    const [sequences, setSequences] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadSequences();
    }, []);

    const loadSequences = async () => {
        setLoading(true);
        try {
            const data = await API.get('/sequences');
            setSequences(data);
        } catch (error) {
            console.error('Failed to load sequences:', error);
        }
        setLoading(false);
    };

    return (
        <div className="view sequences-view">
            <div className="view-header">
                <h1>Email Sequences</h1>
                <button className="btn btn-primary">+ New Sequence</button>
            </div>

            {loading ? (
                <div className="loading">Loading sequences...</div>
            ) : (
                <div className="sequences-list">
                    {sequences.map(sequence => (
                        <div key={sequence.id} className="sequence-card">
                            <h3>{sequence.name}</h3>
                            <p>{sequence.description}</p>
                            <div className="sequence-steps">
                                <strong>Steps:</strong> {sequence.steps?.length || 0}
                            </div>
                            <div className="sequence-steps-list">
                                {sequence.steps?.map(step => (
                                    <div key={step.id} className="step-item">
                                        Step {step.step_order} - Delay: {step.delay_days} days
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

// =============================================================================
// Outbound Control View
// =============================================================================

function OutboundView() {
    const [fromAddress, setFromAddress] = useState('');
    const [dryRun, setDryRun] = useState(true);
    const [running, setRunning] = useState(false);
    const [result, setResult] = useState(null);
    const [config, setConfig] = useState(null);

    useEffect(() => {
        loadConfig();
    }, []);

    const loadConfig = async () => {
        try {
            const data = await API.get('/config');
            setConfig(data);
            if (data.from_addresses.length > 0) {
                setFromAddress(data.from_addresses[0]);
            }
        } catch (error) {
            console.error('Failed to load config:', error);
        }
    };

    const runOutbound = async () => {
        setRunning(true);
        setResult(null);

        try {
            const data = await API.post('/outbound/run', {
                from_address: fromAddress,
                dry_run: dryRun
            });
            setResult(data);
        } catch (error) {
            setResult({ success: false, error: error.message });
        }

        setRunning(false);
    };

    return (
        <div className="view outbound-view">
            <h1>🚀 Outbound Machine</h1>

            <div className="outbound-controls">
                <div className="control-group">
                    <label>From Address</label>
                    <select
                        value={fromAddress}
                        onChange={(e) => setFromAddress(e.target.value)}
                        className="control-select"
                    >
                        {config?.from_addresses.map(addr => (
                            <option key={addr} value={addr}>{addr}</option>
                        ))}
                    </select>
                </div>

                <div className="control-group">
                    <label className="checkbox-label">
                        <input
                            type="checkbox"
                            checked={dryRun}
                            onChange={(e) => setDryRun(e.target.checked)}
                        />
                        Dry Run (don't actually send)
                    </label>
                </div>

                <button
                    className="btn btn-primary btn-large"
                    onClick={runOutbound}
                    disabled={running}
                >
                    {running ? 'Running...' : 'Run Outbound Cycle'}
                </button>
            </div>

            {result && (
                <div className={`result-box ${result.success ? 'success' : 'error'}`}>
                    <h3>{result.success ? '✓ Success' : '✗ Error'}</h3>
                    {result.stats && (
                        <div className="stats-details">
                            <div>Checked: {result.stats.checked}</div>
                            <div>Eligible: {result.stats.eligible}</div>
                            <div>Sent: {result.stats.sent}</div>
                            <div>Failed: {result.stats.failed}</div>
                            <div>Skipped (opted out): {result.stats.skipped_opt_out}</div>
                            <div>Skipped (limit): {result.stats.skipped_limit}</div>
                        </div>
                    )}
                    {result.error && <div className="error-message">{result.error}</div>}
                </div>
            )}

            {config && (
                <div className="info-box">
                    <h3>Configuration</h3>
                    <div>Max emails per day: {config.max_emails_per_day}</div>
                    <div>Physical address: {config.physical_address}</div>
                </div>
            )}
        </div>
    );
}

// =============================================================================
// Settings View
// =============================================================================

function SettingsView() {
    const [config, setConfig] = useState(null);

    useEffect(() => {
        loadConfig();
    }, []);

    const loadConfig = async () => {
        try {
            const data = await API.get('/config');
            setConfig(data);
        } catch (error) {
            console.error('Failed to load config:', error);
        }
    };

    return (
        <div className="view settings-view">
            <h1>⚙️ Settings</h1>

            {config && (
                <div className="settings-sections">
                    <div className="settings-section">
                        <h2>From Addresses</h2>
                        <ul className="address-list">
                            {config.from_addresses.map((addr, idx) => (
                                <li key={idx}>{addr}</li>
                            ))}
                        </ul>
                    </div>

                    <div className="settings-section">
                        <h2>Sending Limits</h2>
                        <p>Max emails per day per address: <strong>{config.max_emails_per_day}</strong></p>
                    </div>

                    <div className="settings-section">
                        <h2>CAN-SPAM Compliance</h2>
                        <p><strong>Company Name:</strong> {config.company_name}</p>
                        <p><strong>Physical Address:</strong><br />{config.physical_address}</p>
                    </div>

                    <div className="settings-section">
                        <h2>Environment</h2>
                        <p className="text-muted">
                            Edit .env file to change configuration settings.
                            Restart the server after making changes.
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
}

// =============================================================================
// Render App
// =============================================================================

ReactDOM.render(<App />, document.getElementById('root'));
