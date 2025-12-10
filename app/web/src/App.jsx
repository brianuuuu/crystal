import React from 'react'
import { ConfigProvider, theme, Layout, App as AntApp } from 'antd'
import Timeline from './pages/Timeline'

const { darkAlgorithm } = theme;

// Custom dark theme configuration
const customTheme = {
    algorithm: darkAlgorithm,
    token: {
        // Colors
        colorPrimary: '#2962ff', // Sharper blue
        colorSuccess: '#00e676', // Bright green for financial up
        colorWarning: '#ffea00', // Bright yellow
        colorError: '#ff1744',   // Bright red for financial down
        colorInfo: '#2962ff',

        // Background colors
        colorBgContainer: '#0f1219', // Deep dark blue-black
        colorBgElevated: '#151922',
        colorBgLayout: '#050510',    // Almost black
        colorBgSpotlight: '#1a1f2b',

        // Text colors
        colorText: '#e0e0e0',
        colorTextSecondary: '#8b9bb4', // Blue-grey tint
        colorTextTertiary: '#5c6b7f',
        colorTextQuaternary: '#3e4756',

        // Border
        colorBorder: '#1f2a3d',
        colorBorderSecondary: '#151c2a',

        // Typography
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        fontSize: 13, // Slightly smaller for compactness

        // Border radius
        borderRadius: 4, // Sharper corners for financial look
        borderRadiusLG: 8,
        borderRadiusSM: 2,

        // Control
        controlHeight: 32, // Compact controls
        controlHeightLG: 40,
        controlHeightSM: 24,
    },
    components: {
        Layout: {
            headerBg: '#0f1219',
            headerPadding: '0 24px',
            siderBg: '#0f1219',
            bodyBg: '#050510',
        },
        Card: {
            colorBgContainer: '#0f1219',
            headerBg: 'transparent',
        },
        Table: {
            colorBgContainer: '#0f1219',
            headerBg: '#151922',
            rowHoverBg: '#1a1f2b',
            headerColor: '#8b9bb4',
        },
        Input: {
            colorBgContainer: '#0a0c10',
            activeBorderColor: '#2962ff',
            hoverBorderColor: '#448aff',
        },
        Select: {
            colorBgContainer: '#0a0c10',
        },
        DatePicker: {
            colorBgContainer: '#0a0c10',
        },
        Modal: {
            contentBg: '#151922',
            headerBg: '#151922',
        },
        Tabs: {
            inkBarColor: '#2962ff',
            itemActiveColor: '#2962ff',
            itemHoverColor: '#448aff',
        },
        Tag: {
            defaultBg: '#151c2a',
        },
        Statistic: {
            titleFontSize: 12,
            contentFontSize: 20,
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
