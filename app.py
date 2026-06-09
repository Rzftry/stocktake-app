import streamlit as st
import requests
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Stocktake Analytics", layout="wide")

st.title("📊 Stocktake Analytics Web App")

url = st.text_input("Paste GitHub RAW TXT URL")

# =========================
# CLEAN NUMBER FUNCTION
# =========================
def fix_num(x):
    if isinstance(x, str) and x.endswith("-"):
        return -float(x.replace("-", ""))
    try:
        return float(x)
    except:
        return 0.0


# =========================
# PARSER ENGINE
# =========================
def parse(txt):

    lines = txt.split("\n")

    data = []
    current = None

    for line in lines:
        line = line.strip()

        if not line:
            continue

        # =========================
        # SKIP NOISE / HEADER BLOCK
        # =========================
        if any(x in line.upper() for x in [
            "DEPT",
            "BRAND DESCRIPTION",
            "SHORT SKU",
            "ACTUAL STOCK",
            "VARIANCE",
            "MARK ON%",
            "QTY",
            "COST (RM)",
            "RETAIL (RM)",
            "REPORT CODE",
            "PRINTED BY",
            "STORE",
            "SELECTION"
        ]):
            continue

        if "<----" in line or "---->" in line or "-----" in line:
            continue

        if "PAGE" in line:
            continue

        # =========================
        # DETECT SKU LINE
        # =========================
        m = re.match(r'^(\d+)\s+(.+?)\s{2,}(.+?)\s+(\d{6,})\s+(.*)$', line)

        if m:
            current = {
                "dept": m.group(1),
                "department": m.group(2),
                "brand": m.group(3),
                "sku": m.group(4),
                "description": m.group(5)
            }
            data.append(current)
            continue

        # =========================
        # DETECT OUTRIGHT / VALUE ROW
        # =========================
        if "Outright:" in line and current:
            nums = re.findall(r'[\d\.\-]+', line)

            if len(nums) >= 10:
                current.update({
                    "actual_qty": fix_num(nums[0]),
                    "actual_cost": fix_num(nums[1]),
                    "actual_retail": fix_num(nums[2]),

                    "ri_qty": fix_num(nums[4]),
                    "ri_cost": fix_num(nums[5]),
                    "ri_retail": fix_num(nums[6]),

                    "var_qty": fix_num(nums[8]),
                    "var_cost": fix_num(nums[9]),
                    "var_retail": fix_num(nums[10]),
                })

    return data


# =========================
# RUN BUTTON
# =========================
if st.button("🚀 Run Parse"):

    if not url:
        st.warning("Please paste GitHub RAW TXT URL")
        st.stop()

    txt = requests.get(url).text
    data = parse(txt)

    df = pd.DataFrame(data)

    # =========================
    # CLEAN TABLES
    # =========================
    variance_df = df[df["var_qty"] != 0]

    # =========================
    # UI LAYOUT
    # =========================
    tab1, tab2, tab3 = st.tabs(["📄 Raw Data", "⚠️ Variance Only", "📊 Summary"])

    with tab1:
        st.subheader("Raw Data")
        st.dataframe(df, use_container_width=True)

    with tab2:
        st.subheader("Variance Only")
        st.dataframe(variance_df, use_container_width=True)

    with tab3:
        st.subheader("Summary")

        st.metric("Total SKU", len(df))
        st.metric("Variance Items", len(variance_df))
        st.metric("Total Cost Variance", round(df["var_cost"].sum(), 2))

    # =========================
    # EXPORT EXCEL
    # =========================
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Raw Data")
        variance_df.to_excel(writer, index=False, sheet_name="Variance Only")

    st.download_button(
        "⬇ Download Excel",
        output.getvalue(),
        file_name="stocktake_analytics.xlsx"
    )
