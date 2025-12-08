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
    xueqiu: { name: '雪球', color: '#ffffff', icon: <StockOutlined /> },
};

// Status icons
const statusIcons = {
    online: <CheckCircleFilled style={{ color: '#10b981' }} />,
    offline: <CloseCircleFilled style={{ color: '#6b6b7a' }} />,
    error: <ExclamationCircleFilled style={{ color: '#ef4444' }} />,
};

// Sentiment Card Component
const SentimentCard = ({ item }) => {
    const platform = platformConfig[item.platform] || { name: item.platform, color: '#666' };

    return (
        <Card
            className="sentiment-card"
            size="small"
            style={{
                marginBottom: 12,
                background: '#16161f',
                borderColor: '#2a2a3a',
                borderLeft: `3px solid ${platform.color}`,
            }}
            hoverable
        >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ flex: 1 }}>
                    {/* Header */}
                    <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8, gap: 8 }}>
                        <Tag color={platform.color} style={{ margin: 0 }}>
                            {platform.icon} {platform.name}
                        </Tag>
                        {item.symbol && (
                            <Tag color="blue" style={{ margin: 0 }}>
                                <StockOutlined /> {item.symbol}
                            </Tag>
                        )}
                        <Text type="secondary" style={{ fontSize: 12 }}>
                            <ClockCircleOutlined style={{ marginRight: 4 }} />
                            {item.posted_at ? dayjs(item.posted_at).format('MM-DD HH:mm') : '-'}
                        </Text>
                    </div>

                    {/* Author */}
                    <div style={{ marginBottom: 8 }}>
                        <Text type="secondary" style={{ fontSize: 13 }}>
                            <UserOutlined style={{ marginRight: 4 }} />
                            {item.author_name || '匿名用户'}
                        </Text>
                    </div>

                    {/* Content */}
                    <Paragraph
                        ellipsis={{ rows: 3, expandable: true, symbol: '展开' }}
                        style={{ marginBottom: 8, color: '#e8e8ec', fontSize: 14 }}
                    >
                        {item.content || '暂无内容'}
                    </Paragraph>

                    {/* Footer */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                        {item.heat_score > 0 && (
                            <Tooltip title="热度分">
                                <Text type="secondary" style={{ fontSize: 12 }}>
                                    <FireOutlined style={{ color: '#f59e0b', marginRight: 4 }} />
                                    {Math.round(item.heat_score)}
                                </Text>
                            </Tooltip>
                        )}
                        {item.topic && (
                            <Tag color="purple" style={{ fontSize: 11 }}># {item.topic}</Tag>
                        )}
                        {item.url && (
                            <a href={item.url} target="_blank" rel="noopener noreferrer">
                                <Text type="secondary" style={{ fontSize: 12 }}>
                                    <LinkOutlined /> 原文
                                </Text>
                            </a>
                        )}
                    </div>
                </div>
            </div>
        </Card>
    );
};

// Account Status Component
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
        message.info(`正在打开 ${platformConfig[selectedPlatform]?.name} 登录页面，请在浏览器中完成登录...`);

        try {
            await axios.post('/api/v1/auth/manual-login', {
                platform: selectedPlatform,
                timeout: 120,
            });
            message.success('登录成功，Cookie 已保存');
            setModalVisible(false);
            onLogin?.();
        } catch (error) {
            const detail = error.response?.data?.detail || '登录超时或失败';
            message.error(detail);
        } finally {
            setLoading(false);
        }
    };

    const selectedAccount = accounts.find((a) => a.platform === selectedPlatform);
    const selectedConfig = platformConfig[selectedPlatform];

    return (
        <>
            <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
                {['weibo', 'zhihu', 'xueqiu'].map((platform) => {
                    const config = platformConfig[platform];
                    const account = accounts.find((a) => a.platform === platform);
                    const isHealthy = account?.is_healthy;
                    const status = isHealthy ? 'online' : 'offline';

                    return (
                        <Tooltip
                            key={platform}
                            title={`${config.name} - 点击查看详情`}
                        >
                            <Button
                                type="text"
                                size="small"
                                onClick={() => handleOpenModal(platform)}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 4,
                                    color: isHealthy ? config.color : '#6b6b7a',
                                }}
                            >
                                {statusIcons[status]}
                                <span style={{ fontSize: 13 }}>{config.name}</span>
                            </Button>
                        </Tooltip>
                    );
                })}
            </div>

            <Modal
                title={
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        {selectedConfig?.icon}
                        <span>{selectedConfig?.name || ''} 账号状态</span>
                    </div>
                }
                open={modalVisible}
                onCancel={() => setModalVisible(false)}
                footer={[
                    <Button key="cancel" onClick={() => setModalVisible(false)}>
                        关闭
                    </Button>,
                    <Button
                        key="login"
                        type="primary"
                        loading={loading}
                        icon={<LoginOutlined />}
                        onClick={handleManualLogin}
                    >
                        {selectedAccount ? '重新登录' : '立即登录'}
                    </Button>,
                ]}
            >
                {selectedAccount ? (
                    <div style={{ padding: '8px 0' }}>
                        <Row gutter={[16, 16]}>
                            <Col span={12}>
                                <div style={{ color: '#8c8c8c', fontSize: 12, marginBottom: 4 }}>账号状态</div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                    {selectedAccount.is_healthy ? (
                                        <>
                                            <CheckCircleFilled style={{ color: '#52c41a' }} />
                                            <span style={{ color: '#52c41a' }}>在线</span>
                                        </>
                                    ) : (
                                        <>
                                            <CloseCircleFilled style={{ color: '#ff4d4f' }} />
                                            <span style={{ color: '#ff4d4f' }}>离线</span>
                                        </>
                                    )}
                                </div>
                            </Col>
                            <Col span={12}>
                                <div style={{ color: '#8c8c8c', fontSize: 12, marginBottom: 4 }}>用户名</div>
                                <div>{selectedAccount.username || '-'}</div>
                            </Col>
                            <Col span={12}>
                                <div style={{ color: '#8c8c8c', fontSize: 12, marginBottom: 4 }}>上次登录</div>
                                <div>
                                    {selectedAccount.last_login_at
                                        ? dayjs(selectedAccount.last_login_at).format('YYYY-MM-DD HH:mm:ss')
                                        : '从未登录'}
                                </div>
                            </Col>
                            <Col span={12}>
                                <div style={{ color: '#8c8c8c', fontSize: 12, marginBottom: 4 }}>最新心跳</div>
                                <div>
                                    {selectedAccount.checked_at
                                        ? dayjs(selectedAccount.checked_at).format('YYYY-MM-DD HH:mm:ss')
                                        : '-'}
                                </div>
                            </Col>
                            {selectedAccount.health_error && (
                                <Col span={24}>
                                    <div style={{ color: '#8c8c8c', fontSize: 12, marginBottom: 4 }}>错误信息</div>
                                    <div style={{ color: '#ff4d4f' }}>{selectedAccount.health_error}</div>
                                </Col>
                            )}
                        </Row>
                    </div>
                ) : (
                    <div style={{ textAlign: 'center', padding: '24px 0', color: '#8c8c8c' }}>
                        <p>该平台尚未配置账号</p>
                        <p>点击"立即登录"按钮开始登录</p>
                    </div>
                )}
            </Modal>
        </>
    );
};



// Main Timeline Component
const Timeline = () => {
    const [loading, setLoading] = useState(false);
    const [items, setItems] = useState([]);
    const [total, setTotal] = useState(0);
    const [accounts, setAccounts] = useState([]);
    const [activeTab, setActiveTab] = useState('all');
    const [dateRange, setDateRange] = useState([
        dayjs().subtract(7, 'day'),
        dayjs(),
    ]);
    const [keyword, setKeyword] = useState('');
    const [symbol, setSymbol] = useState('');
    const [page, setPage] = useState(1);

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
            message.error('获取数据失败');
        } finally {
            setLoading(false);
        }
    }, [activeTab, dateRange, keyword, symbol, page]);

    useEffect(() => {
        fetchAccounts();
    }, [fetchAccounts]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    const handleRefresh = () => {
        fetchData();
        fetchAccounts();
    };

    const handleSearch = (value) => {
        setKeyword(value);
        setPage(1);
    };

    const tabItems = [
        { key: 'all', label: '全部' },
        { key: 'weibo', label: <span><WeiboOutlined /> 微博</span> },
        { key: 'zhihu', label: <span><MessageOutlined /> 知乎</span> },
        { key: 'xueqiu', label: <span><StockOutlined /> 雪球</span> },
    ];

    return (
        <Layout style={{ minHeight: '100vh', background: '#0a0a0f' }}>
            {/* Header */}
            <Header
                style={{
                    background: '#12121a',
                    borderBottom: '1px solid #2a2a3a',
                    padding: '0 24px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    position: 'sticky',
                    top: 0,
                    zIndex: 100,
                }}
            >
                {/* Logo */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div
                        style={{
                            width: 32,
                            height: 32,
                            background: 'linear-gradient(135deg, #00d9ff, #7c3aed)',
                            borderRadius: 8,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                        }}
                    >
                        <span style={{ fontSize: 18 }}>💎</span>
                    </div>
                    <Title level={4} style={{ margin: 0, color: '#e8e8ec' }}>
                        <span className="text-gradient">Crystal</span>
                        <Text type="secondary" style={{ fontSize: 14, marginLeft: 8 }}>
                            舆情哨塔
                        </Text>
                    </Title>
                </div>

                {/* Account Status */}
                <AccountStatus accounts={accounts} onLogin={fetchAccounts} />
            </Header>

            {/* Content */}
            <Content style={{ padding: '24px', maxWidth: 1200, margin: '0 auto', width: '100%' }}>
                {/* Stats */}
                <Row gutter={16} style={{ marginBottom: 24 }}>
                    <Col span={6}>
                        <Card size="small" style={{ background: '#16161f', borderColor: '#2a2a3a' }}>
                            <Statistic
                                title={<Text type="secondary">舆情总数</Text>}
                                value={total}
                                valueStyle={{ color: '#00d9ff' }}
                            />
                        </Card>
                    </Col>
                    <Col span={6}>
                        <Card size="small" style={{ background: '#16161f', borderColor: '#2a2a3a' }}>
                            <Statistic
                                title={<Text type="secondary">在线账号</Text>}
                                value={accounts.filter((a) => a.is_healthy).length}
                                suffix={`/ ${accounts.length}`}
                                valueStyle={{ color: '#10b981' }}
                            />
                        </Card>
                    </Col>
                    <Col span={6}>
                        <Card size="small" style={{ background: '#16161f', borderColor: '#2a2a3a' }}>
                            <Statistic
                                title={<Text type="secondary">时间范围</Text>}
                                value={dateRange?.[0]?.format('MM-DD')}
                                suffix={`至 ${dateRange?.[1]?.format('MM-DD')}`}
                                valueStyle={{ color: '#a0a0b0', fontSize: 16 }}
                            />
                        </Card>
                    </Col>
                    <Col span={6}>
                        <Card size="small" style={{ background: '#16161f', borderColor: '#2a2a3a' }}>
                            <Statistic
                                title={<Text type="secondary">当前平台</Text>}
                                value={activeTab === 'all' ? '全部' : platformConfig[activeTab]?.name}
                                valueStyle={{ color: '#7c3aed', fontSize: 16 }}
                            />
                        </Card>
                    </Col>
                </Row>

                {/* Filters */}
                <Card
                    size="small"
                    style={{
                        marginBottom: 24,
                        background: '#16161f',
                        borderColor: '#2a2a3a',
                    }}
                >
                    <Space wrap size="middle" style={{ width: '100%', justifyContent: 'space-between' }}>
                        <Space wrap>
                            <RangePicker
                                value={dateRange}
                                onChange={setDateRange}
                                style={{ width: 240 }}
                                placeholder={['开始日期', '结束日期']}
                            />
                            <Input
                                placeholder="股票代码"
                                prefix={<StockOutlined />}
                                value={symbol}
                                onChange={(e) => setSymbol(e.target.value)}
                                style={{ width: 140 }}
                                allowClear
                            />
                            <Input.Search
                                placeholder="搜索关键词"
                                prefix={<SearchOutlined />}
                                onSearch={handleSearch}
                                style={{ width: 200 }}
                                allowClear
                            />
                        </Space>
                        <Button
                            icon={<ReloadOutlined />}
                            onClick={handleRefresh}
                        >
                            刷新
                        </Button>
                    </Space>
                </Card>

                {/* Platform Tabs */}
                <Tabs
                    activeKey={activeTab}
                    onChange={(key) => {
                        setActiveTab(key);
                        setPage(1);
                    }}
                    items={tabItems}
                    style={{ marginBottom: 16 }}
                />

                {/* Sentiment List */}
                <Spin spinning={loading}>
                    {items.length > 0 ? (
                        <div className="sentiment-list">
                            {items.map((item, index) => (
                                <SentimentCard key={item.id || index} item={item} />
                            ))}
                        </div>
                    ) : (
                        <Empty
                            description={
                                <Text type="secondary">
                                    暂无舆情数据，请调整筛选条件或等待数据采集
                                </Text>
                            }
                            style={{ marginTop: 80 }}
                        />
                    )}
                </Spin>

                {/* Load More */}
                {items.length > 0 && items.length < total && (
                    <div style={{ textAlign: 'center', marginTop: 24 }}>
                        <Button
                            onClick={() => setPage((p) => p + 1)}
                            loading={loading}
                        >
                            加载更多 ({items.length} / {total})
                        </Button>
                    </div>
                )}
            </Content>

            {/* Footer */}
            <div
                style={{
                    textAlign: 'center',
                    padding: '16px 24px',
                    color: '#6b6b7a',
                    fontSize: 12,
                    borderTop: '1px solid #1f1f2a',
                }}
            >
                Crystal 水晶 - 量化交易舆情监测系统 © {new Date().getFullYear()}
            </div>
        </Layout>
    );
};

export default Timeline;
