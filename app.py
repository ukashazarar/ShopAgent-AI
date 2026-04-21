import streamlit as st
from core.orchestrator import AgentOrchestrator
from config import TRUSTED_DOMAINS

st.set_page_config(
    page_title="Agentic AI Price Finder",
    page_icon="🤖",
    layout="wide"
)

CSS = """
<style>
:root {
  --bg: #f0f4f8; --card: #ffffff; --accent: #6366f1;
  --accent2: #06b6d4; --muted: #64748b;
}
body { background: var(--bg); font-family: 'Segoe UI', sans-serif; }
.main-title {
  font-size: 2.2rem; font-weight: 800;
  background: linear-gradient(90deg, var(--accent), var(--accent2));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  margin-bottom: 4px;
}
.subtitle { color: var(--muted); font-size: 1rem; margin-bottom: 20px; }
.card {
  background: var(--card); padding: 20px; border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.07); margin-bottom: 16px;
}
.best-card {
  background: linear-gradient(135deg, #eef2ff 0%, #e0f2fe 100%);
  border: 2px solid var(--accent); padding: 24px;
  border-radius: 16px; margin-bottom: 20px;
}
.price-big { font-size: 2rem; font-weight: 800; color: #1e293b; }
.price-small { font-size: 1.1rem; font-weight: 700; color: #1e293b; }
.trust-yes { background:#dcfce7; color:#166534; padding:4px 10px; border-radius:999px; font-size:12px; font-weight:600; }
.trust-no  { background:#fef3c7; color:#92400e; padding:4px 10px; border-radius:999px; font-size:12px; font-weight:600; }
.rec-box { background:#f0fdf4; border:1px solid #bbf7d0; border-radius:12px; padding:14px; margin-top:12px; font-size:14px; color:#166534; line-height:1.6; }
a.buy-btn { display:inline-block; background:var(--accent); color:white !important; padding:8px 18px; border-radius:8px; text-decoration:none; font-weight:600; font-size:14px; margin-top:8px; }
.stars { color:#f59e0b; font-size:15px; }
.no-rating { color:var(--muted); font-size:13px; font-style:italic; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# Header
st.markdown("<div class='main-title'>🤖 Agentic AI Price Intelligence</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Type a product name or paste a link — AI agents find you the best deal.</div>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    min_price = st.slider("Min plausible price (₹)", 0, 1000, 50)
    max_results = st.slider("Max results to scan", 5, 40, 20)
    st.divider()
    st.markdown("**Trusted Platforms:**")
    for d in list(TRUSTED_DOMAINS.keys())[:7]:
        st.markdown(f"✅ {d}")
    st.divider()
    st.markdown("**Agent Pipeline:**")
    for step in ["🧠 Planner","🔍 Search","🕷️ Product","📦 Collection","🛡️ Trust","⚖️ Decision","💬 Recommendation"]:
        st.markdown(f"`{step}`")

# Input
col_input, col_btn = st.columns([5, 1])
with col_input:
    user_input = st.text_input(
        "Product",
        placeholder="e.g.  Samsung Galaxy S24  or  https://www.amazon.in/dp/...",
        label_visibility="collapsed"
    )
with col_btn:
    run = st.button("🚀 Search", use_container_width=True)

# Run
if run:
    if not user_input.strip():
        st.warning("Please enter a product name or link.")
    else:
        orchestrator = AgentOrchestrator()

        # Simple progress bar — no threading (fixes Streamlit error)
        steps = [
            "🧠 Planner Agent — understanding query...",
            "🔍 Search Agent — scanning internet...",
            "🕷️ Product Agent — extracting details...",
            "📦 Collection Agent — aggregating listings...",
            "🛡️ Trust Agent — evaluating sources...",
            "⚖️ Decision Agent — AI ranking...",
            "💬 Recommendation Agent — generating explanation...",
        ]

        progress_bar = st.progress(0, text=steps[0])
        status_text = st.empty()

        def update_step(i):
            progress_bar.progress((i + 1) / len(steps), text=steps[min(i, len(steps)-1)])

        update_step(0)

        with st.spinner("Agents working..."):
            result = orchestrator.run(
              user_input,
              min_price=min_price,
              max_results=max_results
)
            product_name, listings, best = result
        progress_bar.progress(1.0, text="✅ Done!")
        # Show error if invalid input
        if isinstance(product_name, str) and listings == [] and best is None:
          st.error(f"❌ {product_name}")
          st.info("💡 Try: 'Samsung Galaxy S24', 'Nike Air Max', 'Sony WH-1000XM5'")
          st.stop()
        status_text.empty()

        # Metrics
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Product", product_name[:28] + "..." if len(product_name) > 28 else product_name)
        with m2:
            st.metric("Listings Found", len(listings))
        with m3:
            trusted_count = sum(1 for l in listings if l.get("is_trusted"))
            st.metric("Trusted Sources", trusted_count)
        with m4:
            if best and best.get("price"):
                st.metric("Best Price", f"₹{int(best['price']):,}")
            else:
                st.metric("Best Price", "—")

        st.divider()

        # Best option
        if best and best.get("price"):
            st.markdown("### 🏆 Best Deal Found")

            is_trusted = best.get("is_trusted", False)
            trust_cls = "trust-yes" if is_trusted else "trust-no"
            trust_label = "Trusted Platform" if is_trusted else "Unverified Source"
            trust_score = best.get("trust_score", 0)

            rating = best.get("rating")
            if rating:
                stars = "★" * int(round(rating)) + "☆" * (5 - int(round(rating)))
                rating_html = f"<span class='stars'>{stars}</span> <span style='font-size:13px;color:#64748b'>({rating}/5)</span>"
            else:
                rating_html = "<span class='no-rating'>Rating not available</span>"

            rec_text = best.get("recommendation_text", "")

            st.markdown(f"""
<div class='best-card'>
  <div style='display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px'>
    <div style='flex:1;min-width:200px'>
      <div style='font-size:1.1rem;font-weight:700;color:#1e293b;margin-bottom:6px'>{best.get('name','')}</div>
      <div style='color:#64748b;font-size:13px;margin-bottom:8px'>{best.get('source','')}</div>
      {rating_html}
      <div style='margin-top:8px'>
        <span class='{trust_cls}'>{trust_label}</span>
        <span style='font-size:12px;color:#94a3b8;margin-left:8px'>Trust: {trust_score}/10</span>
      </div>
    </div>
    <div style='text-align:right'>
      <div class='price-big'>₹{int(best['price']):,}</div>
      <a class='buy-btn' href='{best.get("link","#")}' target='_blank'>Buy Now ➜</a>
    </div>
  </div>
  {"<div class='rec-box'>💡 " + rec_text + "</div>" if rec_text else ""}
</div>
""", unsafe_allow_html=True)

        else:
            st.warning("No listings found. Try a more specific product name (e.g. 'Samsung Galaxy S24 256GB' instead of 'blue shirt')")
            st.info("💡 Tip: Product names with brand + model work best. Clothing/generic terms may not return prices.")

        # All listings
        if listings:
            st.markdown(f"### 📋 All Listings ({len(listings)})")
            col_a, col_b = st.columns(2)
            for i, item in enumerate(listings):
                col = col_a if i % 2 == 0 else col_b
                with col:
                    price = item.get("price")
                    rating = item.get("rating")
                    trust_score = item.get("trust_score", 0)
                    is_trusted = item.get("is_trusted", False)
                    link = item.get("link", "#")
                    name = item.get("name", "Unknown")
                    source = item.get("source", "")

                    trust_cls = "trust-yes" if is_trusted else "trust-no"
                    trust_label = "Trusted" if is_trusted else "Unverified"
                    price_str = f"₹{int(price):,}" if price else "N/A"

                    if rating:
                        stars = "★" * int(round(rating)) + "☆" * (5 - int(round(rating)))
                        rating_html = f"<span class='stars' style='font-size:12px'>{stars}</span> {rating}"
                    else:
                        rating_html = "<span class='no-rating'>No rating</span>"

                    st.markdown(f"""
<div class='card'>
  <div style='display:flex;justify-content:space-between;align-items:center;gap:8px'>
    <div style='flex:1'>
      <div style='font-weight:600;font-size:14px'>
        <a href='{link}' target='_blank' style='color:#6366f1;text-decoration:none'>{name[:65]}</a>
      </div>
      <div style='font-size:12px;color:#64748b;margin:3px 0'>{source}</div>
      <div>{rating_html}</div>
      <div style='margin-top:5px'>
        <span class='{trust_cls}'>{trust_label}</span>
        <span style='font-size:11px;color:#94a3b8;margin-left:6px'>Score: {trust_score}/10</span>
      </div>
    </div>
    <div style='text-align:right;min-width:90px'>
      <div class='price-small'>{price_str}</div>
      <a href='{link}' target='_blank' style='font-size:12px;color:#6366f1'>Buy ➜</a>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)