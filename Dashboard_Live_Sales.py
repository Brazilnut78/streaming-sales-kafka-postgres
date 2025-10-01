import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# Page configuration
st.set_page_config(
    page_title="Real-Time Sales Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database connection parameters
# IMPORTANT: Update these values to match your PostgreSQL setup
DB_CONFIG = {
    'host': 'localhost',
    'database': 'dvdrental',  # Change to your actual database name
    'user': 'postgres',        # Change to your username
    'password': 'CHANGE_ME',  # Change your password
    'port': 5433
}

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Database connection function with caching
@st.cache_resource
def get_db_connection():
    """Create a database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

def fetch_sales_data(conn, limit=1000):
    """Fetch sales data from PostgreSQL"""
    query = f"""
        SELECT id, ts, store_id, amount_usd, channel
        FROM public.sales_events
        ORDER BY ts DESC
        LIMIT {limit};
    """
    try:
        df = pd.read_sql(query, conn)
        df['ts'] = pd.to_datetime(df['ts'])
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

def fetch_summary_stats(conn):
    """Fetch summary statistics"""
    query = """
        SELECT 
            COUNT(*) AS total_sales,
            SUM(amount_usd) AS total_revenue,
            AVG(amount_usd) AS avg_sale,
            MAX(ts) AS latest_sale,
            COUNT(DISTINCT store_id) AS total_stores,
            COUNT(DISTINCT channel) AS total_channels
        FROM public.sales_events;
    """
    try:
        df = pd.read_sql(query, conn)
        return df.iloc[0]
    except Exception as e:
        st.error(f"Error fetching summary: {e}")
        return None

def fetch_sales_by_channel(conn):
    """Fetch sales grouped by channel"""
    query = """
        SELECT 
            channel,
            COUNT(*) AS count,
            SUM(amount_usd) AS revenue
        FROM public.sales_events
        GROUP BY channel
        ORDER BY revenue DESC;
    """
    try:
        return pd.read_sql(query, conn)
    except Exception as e:
        st.error(f"Error fetching channel data: {e}")
        return pd.DataFrame()

def fetch_sales_by_store(conn):
    """Fetch sales grouped by store"""
    query = """
        SELECT 
            store_id,
            COUNT(*) AS count,
            SUM(amount_usd) AS revenue
        FROM public.sales_events
        GROUP BY store_id
        ORDER BY revenue DESC
        LIMIT 10;
    """
    try:
        return pd.read_sql(query, conn)
    except Exception as e:
        st.error(f"Error fetching store data: {e}")
        return pd.DataFrame()

def fetch_recent_sales_trend(conn, hours=24):
    """Fetch sales trend for the last N hours"""
    query = f"""
        SELECT 
            DATE_TRUNC('hour', ts) AS hour,
            COUNT(*) AS sales_count,
            SUM(amount_usd) AS revenue
        FROM public.sales_events
        WHERE ts >= NOW() - INTERVAL '{hours} hours'
        GROUP BY hour
        ORDER BY hour;
    """
    try:
        df = pd.read_sql(query, conn)
        df['hour'] = pd.to_datetime(df['hour'])
        return df
    except Exception as e:
        st.error(f"Error fetching trend data: {e}")
        return pd.DataFrame()

# Main dashboard
def main():
    st.markdown('<div class="main-header">📊 Real-Time Sales Dashboard</div>', unsafe_allow_html=True)
    
    # Sidebar controls
    st.sidebar.header("⚙️ Dashboard Settings")
    auto_refresh = st.sidebar.checkbox("Auto-refresh", value=True)
    refresh_interval = st.sidebar.slider("Refresh interval (seconds)", 1, 30, 5)
    data_limit = st.sidebar.slider("Number of records to display", 100, 5000, 1000, step=100)
    time_range = st.sidebar.selectbox("Time range for trends", [1, 6, 12, 24, 48], index=3)
    
    # Create placeholder for dynamic content
    placeholder = st.empty()
    
    # Get database connection
    conn = get_db_connection()
    
    if conn is None:
        st.error("Cannot connect to database. Please check your connection settings.")
        return
    
    # Auto-refresh loop
    while True:
        with placeholder.container():
            # Fetch data
            summary = fetch_summary_stats(conn)
            sales_df = fetch_sales_data(conn, limit=data_limit)
            channel_df = fetch_sales_by_channel(conn)
            store_df = fetch_sales_by_store(conn)
            trend_df = fetch_recent_sales_trend(conn, hours=time_range)
            
            if summary is not None and not sales_df.empty:
                # Display summary metrics
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.metric("Total Sales", f"{summary['total_sales']:,}")
                with col2:
                    st.metric("Total Revenue", f"${summary['total_revenue']:,.2f}")
                with col3:
                    st.metric("Avg Sale", f"${summary['avg_sale']:.2f}")
                with col4:
                    st.metric("Active Stores", f"{summary['total_stores']}")
                with col5:
                    st.metric("Channels", f"{summary['total_channels']}")
                
                # Last update time
                st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                st.caption(f"Latest sale: {summary['latest_sale']}")
                
                st.divider()
                
                # Charts in columns
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📈 Sales Trend (Last {} Hours)".format(time_range))
                    if not trend_df.empty:
                        fig_trend = go.Figure()
                        fig_trend.add_trace(go.Scatter(
                            x=trend_df['hour'],
                            y=trend_df['sales_count'],
                            mode='lines+markers',
                            name='Sales Count',
                            line=dict(color='#1f77b4', width=3),
                            marker=dict(size=8)
                        ))
                        fig_trend.update_layout(
                            xaxis_title="Time",
                            yaxis_title="Number of Sales",
                            hovermode='x unified',
                            height=400
                        )
                        st.plotly_chart(fig_trend, use_container_width=True)
                    else:
                        st.info("No trend data available")
                
                with col2:
                    st.subheader("💰 Revenue Trend (Last {} Hours)".format(time_range))
                    if not trend_df.empty:
                        fig_revenue = go.Figure()
                        fig_revenue.add_trace(go.Scatter(
                            x=trend_df['hour'],
                            y=trend_df['revenue'],
                            mode='lines+markers',
                            name='Revenue',
                            line=dict(color='#2ca02c', width=3),
                            marker=dict(size=8),
                            fill='tozeroy'
                        ))
                        fig_revenue.update_layout(
                            xaxis_title="Time",
                            yaxis_title="Revenue ($)",
                            hovermode='x unified',
                            height=400
                        )
                        st.plotly_chart(fig_revenue, use_container_width=True)
                    else:
                        st.info("No revenue data available")
                
                st.divider()
                
                # More charts
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📺 Sales by Channel")
                    if not channel_df.empty:
                        fig_channel = px.pie(
                            channel_df,
                            values='revenue',
                            names='channel',
                            title='Revenue Distribution by Channel',
                            hole=0.4,
                            color_discrete_sequence=px.colors.qualitative.Set3
                        )
                        fig_channel.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig_channel, use_container_width=True)
                    else:
                        st.info("No channel data available")
                
                with col2:
                    st.subheader("🏪 Top 10 Stores by Revenue")
                    if not store_df.empty:
                        fig_store = px.bar(
                            store_df,
                            x='store_id',
                            y='revenue',
                            title='Top Performing Stores',
                            labels={'store_id': 'Store ID', 'revenue': 'Revenue ($)'},
                            color='revenue',
                            color_continuous_scale='Blues'
                        )
                        fig_store.update_layout(showlegend=False, height=400)
                        st.plotly_chart(fig_store, use_container_width=True)
                    else:
                        st.info("No store data available")
                
                st.divider()
                
                # Recent transactions table
                st.subheader("📋 Recent Transactions")
                st.dataframe(
                    sales_df.head(50),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "id": "ID",
                        "ts": st.column_config.DatetimeColumn("Timestamp", format="YYYY-MM-DD HH:mm:ss"),
                        "store_id": "Store ID",
                        "amount_usd": st.column_config.NumberColumn("Amount", format="$%.2f"),
                        "channel": "Channel"
                    }
                )
                
                # Download button
                csv = sales_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Full Data as CSV",
                    data=csv,
                    file_name=f"sales_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            else:
                st.warning("No data available. Make sure your Kafka producer is running and data is flowing into PostgreSQL.")
        
        # Auto-refresh logic
        if not auto_refresh:
            break
        
        time.sleep(refresh_interval)
        
        # Force rerun
        st.rerun()

if __name__ == "__main__":
    main()