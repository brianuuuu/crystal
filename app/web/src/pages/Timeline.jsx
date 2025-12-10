import React, { useState, useEffect, useCallback } from 'react';
import {
    Layout,
    Card,
    Tabs,
    DatePicker,
    Input,
    Select,
    Space,
    Badge,
    Tag,
    Typography,
    Spin,
    Empty,
    Tooltip,
    Button,
    Modal,
    Form,
    message,
    Row,
    Col,
    Statistic,
    Divider,
} from 'antd';
import {
    SearchOutlined,
    ReloadOutlined,
    UserOutlined,
    WeiboOutlined,
    MessageOutlined,
    StockOutlined,
    FireOutlined,
    ClockCircleOutlined,
    LinkOutlined,
    CheckCircleFilled,
    CloseCircleFilled,
    ExclamationCircleFilled,
    LoginOutlined,
    CloudDownloadOutlined,
    PlusOutlined,
    EditOutlined,
    DeleteOutlined,
    GlobalOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import axios from 'axios';

const { Header, Content } = Layout;
const { Title, Text, Paragraph } = Typography;
const { RangePicker } = DatePicker;

// Platform icons and colors
const platformConfig = {
    weibo: { name: '微博', color: '#e6162d', icon: <WeiboOutlined /> },
    zhihu: { name: '知乎', color: '#0084ff', icon: <MessageOutlined /> },
    xueqiu: { name: '雪球', color: '#f59e0b', icon: <StockOutlined /> },
};

// Status icons
const statusIcons = {
    online: <CheckCircleFilled style={{ color: 'var(--accent-success)' }} />,
    offline: <CloseCircleFilled style={{ color: 'var(--text-muted)' }} />,
    error: <ExclamationCircleFilled style={{ color: 'var(--accent-error)' }} />,
};

// Compact Sentiment Card Component
const SentimentCard = ({ item }) => {
    const platform = platformConfig[item.platform] || { name: item.platform, color: '#666' };

    return (
        <div className="sentiment-card" style={{ padding: '12px 16px', marginBottom: 1 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
                <div style={{ flex: 1 }}>
                    {/* Header Line: Platform | Symbol | Time | Author */}
                    <div style={{ display: 'flex', alignItems: 'center', marginBottom: 6, gap: 12, fontSize: 12, color: 'var(--text-muted)' }}>
                        <Space size={4} style={{ color: platform.color, fontWeight: 600 }}>
                            {platform.icon}
                            <span>{platform.name}</span>
                        </Space>

                        <Divider type="vertical" style={{ borderColor: 'var(--border-subtle)', margin: 0 }} />

                        {item.symbol && (
                            <span className="mono" style={{ color: 'var(--text-secondary)' }}>
                                {item.symbol}
                            </span>
                        )}

                        <span className="mono">
                            {item.posted_at ? dayjs(item.posted_at).format('HH:mm:ss') : '-'}
                        </span>

                        <span>
                            {item.author_name || 'Anonymous'}
                        </span>

                        {item.topic && (
                            <span style={{ color: 'var(--accent-secondary)' }}>#{item.topic}</span>
                        )}

                        {item.heat_score > 0 && (
                            <Space size={2} style={{ color: 'var(--accent-warning)', marginLeft: 'auto' }}>
                                <FireOutlined />
                                <span className="mono">{Math.round(item.heat_score)}</span>
                            </Space>
                        )}
                    </div>

                    {/* Content */}
                    <Paragraph
                        ellipsis={{ rows: 2, expandable: true, symbol: 'More' }}
                        style={{ marginBottom: 4, color: 'var(--text-primary)', fontSize: 14, lineHeight: 1.5 }}
                    >
                        {item.content || 'Content empty'}
                    </Paragraph>

                    {/* Footer Actions (Optional/Hover) */}
                    {item.url && (
                        <div style={{ marginTop: 4 }}>
                            <a href={item.url} target="_blank" rel="noopener noreferrer" style={{ fontSize: 12, display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                                <LinkOutlined /> Source
                            </a>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

// Account Status Component (Compact)
const AccountStatus = ({ accounts, onLogin }) => {
    const [loading, setLoading] = useState(false);
    const [modalVisible, setModalVisible] = useState(false);
    const [selectedPlatform, setSelectedPlatform] = useState(null);

    const handleOpenModal = (platform) => {
        setSelectedPlatform(platform);
        setModalVisible(true);
    };

    const handleManualLogin = async () => {
        if (!selectedPlatform) return;

        setLoading(true);
        message.info(`Opening ${platformConfig[selectedPlatform]?.name} login page...`);

        try {
            await axios.post('/api/v1/auth/manual-login', {
                platform: selectedPlatform,
                timeout: 120,
            });
            message.success('Login successful, cookie saved');
            setModalVisible(false);
            onLogin?.();
        } catch (error) {
            const detail = error.response?.data?.detail || 'Login timeout or failed';
            message.error(detail);
        } finally {
            setLoading(false);
        }
    };

    const selectedAccount = accounts.find((a) => a.platform === selectedPlatform);
    const selectedConfig = platformConfig[selectedPlatform];

    return (
        <>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                {['weibo', 'zhihu', 'xueqiu'].map((platform) => {
                    const config = platformConfig[platform];
                    const account = accounts.find((a) => a.platform === platform);
                    const isHealthy = account?.is_healthy;
                    const status = isHealthy ? 'online' : 'offline';

                    return (
                        <Tooltip
                            key={platform}
                            title={`${config.name} - Click for details`}
                        >
                            <Button
                                type="text"
                                size="small"
                                onClick={() => handleOpenModal(platform)}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 6,
                                    padding: '0 8px',
                                    color: isHealthy ? config.color : 'var(--text-muted)',
                                    background: 'var(--bg-secondary)',
                                    border: '1px solid var(--border-subtle)',
                                }}
                            >
                                {statusIcons[status]}
                                <span style={{ fontSize: 12 }}>{config.name}</span>
                            </Button>
                        </Tooltip>
                    );
                })}
            </div>

            <Modal
                title={
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        {selectedConfig?.icon}
                        <span>{selectedConfig?.name || ''} Account Status</span>
                    </div>
                }
                open={modalVisible}
                onCancel={() => setModalVisible(false)}
                footer={[
                    <Button key="cancel" onClick={() => setModalVisible(false)}>
                        Close
                    </Button>,
                    <Button
                        key="login"
                        type="primary"
                        loading={loading}
                        icon={<LoginOutlined />}
                        onClick={handleManualLogin}
                    >
                        {selectedAccount ? 'Re-login' : 'Login Now'}
                    </Button>,
                ]}
            >
                {/* Modal content kept similar to verify functionality, can be compacted if needed */}
                {selectedAccount ? (
                    <div style={{ padding: '8px 0' }}>
                        <Row gutter={[16, 16]}>
                            <Col span={12}>
                                <div style={{ color: '#8c8c8c', fontSize: 12, marginBottom: 4 }}>Status</div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                    {selectedAccount.is_healthy ? <span style={{ color: '#52c41a' }}>Online</span> : <span style={{ color: '#ff4d4f' }}>Offline</span>}
                                </div>
                            </Col>
                            <Col span={12}>
                                <div style={{ color: '#8c8c8c', fontSize: 12, marginBottom: 4 }}>Username</div>
                                <div>{selectedAccount.username || '-'}</div>
                            </Col>
                            <Col span={12}>
                                <div style={{ color: '#8c8c8c', fontSize: 12, marginBottom: 4 }}>Last Login</div>
                                <div>{selectedAccount.last_login_at ? dayjs(selectedAccount.last_login_at).format('YYYY-MM-DD HH:mm') : '-'}</div>
                            </Col>
                            <Col span={12}>
                                <div style={{ color: '#8c8c8c', fontSize: 12, marginBottom: 4 }}>Last Check</div>
                                <div>{selectedAccount.checked_at ? dayjs(selectedAccount.checked_at).format('YYYY-MM-DD HH:mm') : '-'}</div>
                            </Col>
                        </Row>
                    </div>
                ) : (
                    <div style={{ textAlign: 'center', padding: '24px 0', color: '#8c8c8c' }}>
                        <p>No account configured</p>
                    </div>
                )}
            </Modal>
        </>
    );
};


// Watchlist Panel Component
const WatchlistPanel = () => {
    const [watchlist, setWatchlist] = useState({});
    const [activeTab, setActiveTab] = useState('weibo');
    const [loading, setLoading] = useState(false);
    const [modalVisible, setModalVisible] = useState(false);
    const [editingItem, setEditingItem] = useState(null);
    const [form] = Form.useForm();

    const fetchWatchlist = useCallback(async () => {
        setLoading(true);
        try {
            const response = await axios.get('/api/v1/watchlist/all');
            setWatchlist(response.data || {});
        } catch (error) {
            console.error('Failed to fetch watchlist:', error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchWatchlist();
    }, [fetchWatchlist]);

    const handleAdd = () => {
        setEditingItem(null);
        form.resetFields();
        form.setFieldsValue({ platform: activeTab, target_type: 'account' });
        setModalVisible(true);
    };

    const handleEdit = (item) => {
        setEditingItem(item);
        form.setFieldsValue(item);
        setModalVisible(true);
    };

    const handleDelete = async (id) => {
        try {
            await axios.delete(`/api/v1/watchlist/${id}`);
            message.success('Deleted');
            fetchWatchlist();
        } catch (error) {
            message.error('Delete failed');
        }
    };

    const handleSubmit = async () => {
        try {
            const values = await form.validateFields();
            if (editingItem) {
                await axios.put(`/api/v1/watchlist/${editingItem.id}`, values);
                message.success('Updated');
            } else {
                await axios.post('/api/v1/watchlist', values);
                message.success('Added');
            }
            setModalVisible(false);
            fetchWatchlist();
        } catch (error) {
            message.error('Save failed');
        }
    };

    const currentList = watchlist[activeTab] || [];

    return (
        <Card
            className="crystal-card"
            title={
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: 14 }}>Watchlist</span>
                    <Button type="text" size="small" icon={<PlusOutlined />} onClick={handleAdd} />
                </div>
            }
            size="small"
            style={{ height: '100%', border: 'none', background: 'transparent' }}
            headStyle={{ borderBottom: '1px solid var(--border-subtle)', minHeight: 40, padding: '0 12px' }}
            bodyStyle={{ padding: 0 }}
        >
            <Tabs
                activeKey={activeTab}
                onChange={setActiveTab}
                size="small"
                style={{ padding: '0 12px', marginBottom: 8 }}
                items={[
                    { key: 'weibo', label: 'Weibo' },
                    { key: 'zhihu', label: 'Zhihu' },
                    { key: 'xueqiu', label: 'Xueqiu' },
                ]}
            />
            <div style={{ maxHeight: 600, overflowY: 'auto', padding: '0 12px 12px' }}>
                {loading ? (
                    <div style={{ textAlign: 'center', padding: 24 }}><Spin size="small" /></div>
                ) : currentList.length === 0 ? (
                    <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No Items" style={{ margin: '24px 0' }} />
                ) : (
                    currentList.map((item) => (
                        <div
                            key={item.id}
                            style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                padding: '8px 10px',
                                background: 'var(--bg-card)',
                                border: '1px solid var(--border-subtle)',
                                borderRadius: 4,
                                marginBottom: 6,
                            }}
                        >
                            <div style={{ flex: 1, overflow: 'hidden' }}>
                                <div style={{ color: 'var(--text-primary)', fontSize: 13, fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{item.display_name}</div>
                                <div style={{ color: 'var(--text-muted)', fontSize: 11 }} className="mono">
                                    {item.target_type === 'account' && item.external_id}
                                    {item.target_type === 'symbol' && `$${item.symbol}`}
                                    {item.target_type === 'keyword' && `#${item.keyword}`}
                                </div>
                            </div>
                            <Space size={2}>
                                <Button type="text" size="small" icon={<EditOutlined style={{ fontSize: 12 }} />} onClick={() => handleEdit(item)} />
                                <Button type="text" size="small" danger icon={<DeleteOutlined style={{ fontSize: 12 }} />} onClick={() => handleDelete(item.id)} />
                            </Space>
                        </div>
                    ))
                )}
            </div>

            <Modal
                title={editingItem ? 'Edit Watch Item' : 'Add Watch Item'}
                open={modalVisible}
                onCancel={() => setModalVisible(false)}
                onOk={handleSubmit}
                width={400}
            >
                <Form form={form} layout="vertical" size="small">
                    <Form.Item name="platform" label="Platform" rules={[{ required: true }]}>
                        <Select options={[{ value: 'weibo', label: 'Weibo' }, { value: 'zhihu', label: 'Zhihu' }, { value: 'xueqiu', label: 'Xueqiu' }]} />
                    </Form.Item>
                    <Form.Item name="target_type" label="Type" rules={[{ required: true }]}>
                        <Select options={[{ value: 'account', label: 'User' }, { value: 'symbol', label: 'Symbol' }, { value: 'keyword', label: 'Keyword' }]} />
                    </Form.Item>
                    <Form.Item name="display_name" label="Display Name" rules={[{ required: true }]}>
                        <Input />
                    </Form.Item>
                    <Form.Item name="external_id" label="User ID (Optional)">
                        <Input placeholder="UID / url_token" />
                    </Form.Item>
                    <Form.Item name="symbol" label="Symbol (Optional)">
                        <Input placeholder="e.g SH600036" />
                    </Form.Item>
                    <Form.Item name="keyword" label="Keyword (Optional)">
                        <Input />
                    </Form.Item>
                </Form>
            </Modal>
        </Card>
    );
};


// Main Timeline Component
const Timeline = () => {
    const [loading, setLoading] = useState(false);
    const [items, setItems] = useState([]);
    const [total, setTotal] = useState(0);
    const [accounts, setAccounts] = useState([]);
    const [activeTab, setActiveTab] = useState('all');
    const [dateRange, setDateRange] = useState([dayjs(), dayjs()]);
    const [keyword, setKeyword] = useState('');
    const [symbol, setSymbol] = useState('');
    const [page, setPage] = useState(1);
    const [crawling, setCrawling] = useState(false);

    // Fetch accounts status
    const fetchAccounts = useCallback(async () => {
        try {
            const response = await axios.get('/api/v1/auth/status');
            setAccounts(response.data.accounts || []);
        } catch (error) {
            console.error('Failed to fetch accounts:', error);
        }
    }, []);

    // Fetch sentiment data
    const fetchData = useCallback(async () => {
        setLoading(true);
        try {
            const params = {
                page,
                page_size: 50,
            };

            if (activeTab !== 'all') {
                params.platform = activeTab;
            }
            if (dateRange?.[0]) {
                params.from = dateRange[0].format('YYYY-MM-DD');
            }
            if (dateRange?.[1]) {
                params.to = dateRange[1].format('YYYY-MM-DD');
            }
            if (keyword) {
                params.keyword = keyword;
            }
            if (symbol) {
                params.symbol = symbol;
            }

            const response = await axios.get('/api/v1/snapshot', { params });
            setItems(response.data.items || []);
            setTotal(response.data.total || 0);
        } catch (error) {
            console.error('Failed to fetch data:', error);
            message.error('Data fetch failed');
        } finally {
            setLoading(false);
        }
    }, [activeTab, dateRange, keyword, symbol, page]);

    useEffect(() => { fetchAccounts(); }, [fetchAccounts]);
    useEffect(() => { fetchData(); }, [fetchData]);

    const handleRefresh = () => { fetchData(); fetchAccounts(); };

    const handleCrawl = async () => {
        const platform = activeTab === 'all' ? 'all' : activeTab;
        setCrawling(true);
        message.info(`Crawling ${platform === 'all' ? 'All' : platform}...`);

        try {
            const response = await axios.post(`/api/v1/crawl?platform=${platform}`);
            const result = response.data;
            message.success(`Done! Saved ${result.total_saved} items`);
            fetchData();
        } catch (error) {
            message.error('Crawl failed');
        } finally {
            setCrawling(false);
        }
    };

    const handleSearch = (value) => { setKeyword(value); setPage(1); };

    return (
        <Layout style={{ minHeight: '100vh' }}>
            {/* Compact Header */}
            <Header
                style={{
                    height: 48,
                    lineHeight: '48px',
                    padding: '0 16px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    position: 'sticky',
                    top: 0,
                    zIndex: 100,
                    borderBottom: '1px solid var(--border-color)',
                    background: 'rgba(15, 18, 25, 0.9)',
                    backdropFilter: 'blur(8px)',
                }}
            >
                {/* Logo Area */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{ display: 'flex', alignItems: 'center', color: 'var(--accent-primary)', fontSize: 18 }}>
                        <GlobalOutlined spin={crawling} />
                    </div>
                    <span style={{ fontSize: 16, fontWeight: 600, letterSpacing: '0.5px' }} className="text-gradient">CRYSTAL</span>
                    <Divider type="vertical" />
                    {/* Compact Stats in Header */}
                    <Space size={16} split={<Divider type="vertical" style={{ borderColor: 'var(--border-subtle)' }} />}>
                        <Space size={4} style={{ fontSize: 12 }}>
                            <span style={{ color: 'var(--text-muted)' }}>Total:</span>
                            <span className="mono" style={{ color: 'var(--accent-primary)' }}>{total}</span>
                        </Space>
                        <Space size={4} style={{ fontSize: 12 }}>
                            <span style={{ color: 'var(--text-muted)' }}>Accounts:</span>
                            <span className="mono" style={{ color: 'var(--accent-success)' }}>{accounts.filter(a => a.is_healthy).length}/{accounts.length}</span>
                        </Space>
                        <Space size={4} style={{ fontSize: 12 }}>
                            <span style={{ color: 'var(--text-muted)' }}>API:</span>
                            <span style={{ color: 'var(--accent-success)' }}>●</span>
                        </Space>
                        <Space size={4} style={{ fontSize: 12 }}>
                            <span style={{ color: 'var(--text-muted)' }}>Sync:</span>
                            <span className="mono">{dayjs().format('HH:mm')}</span>
                        </Space>
                        <Space size={4} style={{ fontSize: 12 }}>
                            <span style={{ color: 'var(--text-muted)' }}>Mem:</span>
                            <span className="mono">24%</span>
                        </Space>
                    </Space>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                    <AccountStatus accounts={accounts} onLogin={fetchAccounts} />

                    <Button
                        type="primary"
                        size="small"
                        icon={<CloudDownloadOutlined />}
                        loading={crawling}
                        onClick={handleCrawl}
                    >
                        Sync
                    </Button>
                </div>
            </Header>

            {/* Main Content */}
            <Content style={{ padding: '0 16px 16px', maxWidth: 1600, margin: '0 auto', width: '100%' }}>
                <Row gutter={16}>
                    <Col xs={24} lg={18}>
                        {/* Toolbar */}
                        <div style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            padding: '12px 0',
                            marginBottom: 8,
                            borderBottom: '1px solid var(--border-subtle)'
                        }}>
                            <Space size={12}>
                                <Tabs
                                    activeKey={activeTab}
                                    onChange={(key) => { setActiveTab(key); setPage(1); }}
                                    size="small"
                                    type="card"
                                    tabBarStyle={{ marginBottom: 0 }}
                                    items={[
                                        { key: 'all', label: 'All' },
                                        { key: 'weibo', label: <span><WeiboOutlined /> Weibo</span> },
                                        { key: 'zhihu', label: <span><MessageOutlined /> Zhihu</span> },
                                        { key: 'xueqiu', label: <span><StockOutlined /> Xueqiu</span> },
                                    ]}
                                />
                                <Divider type="vertical" />
                                <RangePicker
                                    value={dateRange}
                                    onChange={setDateRange}
                                    size="small"
                                    style={{ width: 220 }}
                                    bordered={false}
                                />
                            </Space>

                            <Space>
                                <Input
                                    placeholder="Symbol"
                                    prefix={<StockOutlined style={{ color: 'var(--text-muted)' }} />}
                                    value={symbol}
                                    onChange={(e) => setSymbol(e.target.value)}
                                    size="small"
                                    style={{ width: 100, background: 'transparent' }}
                                    bordered={false}
                                />
                                <Input.Search
                                    placeholder="Search keywords..."
                                    onSearch={handleSearch}
                                    size="small"
                                    style={{ width: 160 }}
                                    allowClear
                                />
                                <Button size="small" icon={<ReloadOutlined />} onClick={handleRefresh} />
                            </Space>
                        </div>

                        {/* Sentiment List */}
                        <Spin spinning={loading}>
                            <div className="sentiment-list" style={{ minHeight: 400 }}>
                                {items.length > 0 ? (
                                    items.map((item, index) => (
                                        <SentimentCard key={item.id || index} item={item} />
                                    ))
                                ) : (
                                    <Empty description={<span style={{ color: 'var(--text-muted)' }}>No Data</span>} style={{ marginTop: 60 }} />
                                )}
                            </div>
                        </Spin>

                        {/* Pagination/Load More */}
                        {items.length > 0 && items.length < total && (
                            <div style={{ textAlign: 'center', marginTop: 16, marginBottom: 24 }}>
                                <Button onClick={() => setPage(p => p + 1)} loading={loading} type="dashed" size="small" style={{ width: 200 }}>
                                    Load More
                                </Button>
                            </div>
                        )}
                    </Col>

                    {/* Right Sider - Watchlist */}
                    <Col xs={24} lg={6} style={{ borderLeft: '1px solid var(--border-subtle)', paddingLeft: 16, marginTop: 12 }}>
                        <WatchlistPanel />
                    </Col>
                </Row>
            </Content>
        </Layout>
    );
};

export default Timeline;

