import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from scanner_live import run_full_scan, get_nifty500_symbols

st.set_page_config(page_title="Nifty500 Live Swing Scanner", page_icon="📈", layout="wide")

st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem; font-weight: 700;
        background: linear-gradient(90deg, #1f77b4, #2ca02c);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">📈 Nifty500 Live Swing Scanner</div>', unsafe_allow_html=True)
st.caption(f"Scan time: {datetime.now().strftime('%d %b %Y, %H:%M')} | Data: Yahoo Finance (delayed ~15 min)")

# ---------- SIDEBAR ----------
st.sidebar.header("⚙️ Scan Settings")
max_stocks = st.sidebar.slider("Max stocks to scan", 50, 500, 100, 50)
min_score = st.sidebar.slider("Min Score", 3, 5, 3)
min_rr = st.sidebar.slider("Min R:R Ratio", 0.0, 5.0, 1.5, 0.1)

if st.sidebar.button("🚀 Run Live Scan", type="primary"):
    with st.spinner(f"Scanning {max_stocks} stocks... (2-3 min lagenge)"):
        symbols = get_nifty500_symbols()[:max_stocks]
        df = run_full_scan(symbols)

        if df.empty:
            st.error("Koi stock nahi mila. Settings change karo ya baad me try karo.")
        else:
            st.session_state["scan_df"] = df
            st.success(f"✅ Scan complete! {len(df)} stocks mile.")

# ---------- RESULTS ----------
if "scan_df" in st.session_state:
    df = st.session_state["scan_df"]
    fdf = df[(df["Score"] >= min_score) & (df["RR_Ratio"] >= min_rr)]

    # Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Found", len(df))
    c2.metric("Filtered", len(fdf))
    c3.metric("BUY Signals", int((fdf["Signal"] == "BUY").sum()))
    c4.metric("Avg Upside %", f"{fdf['Upside_%'].mean():.2f}%" if len(fdf) else "—")

    st.divider()

    # Tabs
    t1, t2, t3 = st.tabs(["📋 Stocks", "📊 Charts", "🔥 Top Picks"])

    with t1:
        st.dataframe(
            fdf[["Symbol", "Signal", "Score", "Entry", "StopLoss", "Target",
                  "RR_Ratio", "Upside_%", "Reasons"]].reset_index(drop=True),
            use_container_width=True, height=600,
            column_config={
                "Entry": st.column_config.NumberColumn("Entry ₹", format="₹%.2f"),
                "StopLoss": st.column_config.NumberColumn("SL ₹", format="₹%.2f"),
                "Target": st.column_config.NumberColumn("Target ₹", format="₹%.2f"),
                "Upside_%": st.column_config.NumberColumn("Upside %", format="%.2f%%"),
                "RR_Ratio": st.column_config.NumberColumn("R:R", format="%.2f"),
            }
        )
        csv = fdf.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv,
                           f"scan_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", "text/csv")

    with t2:
        if not fdf.empty:
            fig = px.bar(
                fdf.sort_values("Upside_%", ascending=False).head(15),
                x="Symbol", y="Upside_%", color="Signal",
                title="Top 15 by Upside %"
            )
            st.plotly_chart(fig, use_container_width=True)

    with t3:
        top = fdf.sort_values(["Score", "RR_Ratio"], ascending=[False, False]).head(10)
        for _, row in top.iterrows():
            with st.container(border=True):
                c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
                c1.markdown(f"### {row['Symbol']}  \n`{row['Signal']}` · Score **{int(row['Score'])}**")
                c2.metric("Entry", f"₹{row['Entry']:.2f}")
                c3.metric("Target", f"₹{row['Target']:.2f}", f"+{row['Upside_%']:.1f}%")
                c4.metric("Stop", f"₹{row['StopLoss']:.2f}")
                c5.metric("R:R", f"{row['RR_Ratio']:.2f}")
                st.caption(f"**Reasons:** {row['Reasons']}")
else:
    st.info("👈 Sidebar me **Run Live Scan** click karo. Pehla scan 2-3 minute lega.")
