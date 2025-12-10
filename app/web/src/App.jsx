import React from 'react'
import { ConfigProvider, theme, Layout, App as AntApp } from 'antd'
import Timeline from './pages/Timeline'

const { darkAlgorithm } = theme;

// Custom dark theme configuration
const customTheme = {
    algorithm: darkAlgorithm,
    token: {
        // Colors
        colorPrimary: '#3673f5',
        colorSuccess: '#10b981',
        colorWarning: '#f59e0b',
        colorError: '#ef4444',
        colorInfo: '#3673f5',

        // Background colors
        colorBgContainer: '#16161f',
        colorBgElevated: '#1a1a24',
        colorBgLayout: '#0a0a0f',
        colorBgSpotlight: '#12121a',

        // Text colors
        colorText: '#e8e8ec',
        colorTextSecondary: '#a0a0b0',
        colorTextTertiary: '#6b6b7a',
        colorTextQuaternary: '#4a4a5a',

        // Border
        colorBorder: '#2a2a3a',
        colorBorderSecondary: '#1f1f2a',

        // Typography
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        fontSize: 14,

        // Border radius
        borderRadius: 8,
        borderRadiusLG: 12,
        borderRadiusSM: 6,

        // Control
        controlHeight: 36,
        controlHeightLG: 44,
        controlHeightSM: 28,
    },
    components: {
        Layout: {
            headerBg: '#12121a',
            siderBg: '#12121a',
            bodyBg: '#0a0a0f',
        },
        Card: {
            colorBgContainer: '#16161f',
        },
        Table: {
            colorBgContainer: '#16161f',
            headerBg: '#1a1a24',
            rowHoverBg: '#1f1f2a',
        },
        Input: {
            colorBgContainer: '#1a1a24',
        },
        Select: {
            colorBgContainer: '#1a1a24',
        },
        DatePicker: {
            colorBgContainer: '#1a1a24',
        },
        Modal: {
            contentBg: '#16161f',
            headerBg: '#16161f',
        },
        Tabs: {
            inkBarColor: '#3673f5',
            itemActiveColor: '#3673f5',
            itemHoverColor: '#5a8df7',
        },
        Tag: {
            defaultBg: '#1a1a24',
        },
        Badge: {
            statusSize: 8,
        },
    },
};

function App() {
    return (
        <ConfigProvider theme={customTheme}>
            <AntApp>
                <Layout style={{ minHeight: '100vh' }}>
                    <Timeline />
                </Layout>
            </AntApp>
        </ConfigProvider>
    )
}

export default App
