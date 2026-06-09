import streamlit as st
import requests
import pandas as pd
import re
from io import BytesIO

st.title("📊 Stocktake Analytics Pro")

# =========================
# INPUT SECTION
# =========================
option = st.radio("Select input method:", ["GitHub URL", "Upload File"])

txt = None

if option == "GitHub URL":
    url = st.text_input("Paste GitHub RAW URL")
    if url:
        try:
            txt = requests.get(url).text
        except:
            st.error("Failed to load URL")

else:
    file = st.file_uploader("Upload TXT file", type=["txt"])
    if file:
        txt = file.read().decode("utf-8")


# =========================
# FUNCTIONS
# =========================
def fix_num(x):
    if x is None:
        return 0.0

    x = str(x).strip()

    if x.endswith("-"):
        try:
            return -float(x[:-1])
        except:
            return 0.0

    try:
        return float(x)
    except:
        return 0.0


def parse(txt):
    lines = txt.split("\n")

    items = []
    current = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if "PAGE" in line or "Report Code" in line:
            continue

        m = re.match(r'^(\d+)\s+(.+?)\s{2,}(.+?)\s+(\d{5,})\s+(.*)$', line)

        if m:
            current = {
                "dept": m.group(1),
                "brand": m.group(3),
                "sku": m.group(4),
                "desc": m.group(5)
            }
            items.append(current)
            continue

        if "Outright:" in line and current:
            nums = re.findall(r'-?\d+\.?\d*', line)

            if len(nums) >= 12:
                keys = [
                    "actual_qty", "actual_cost", "actual_retail", "actual_markon",
                    "ri_qty", "ri_cost", "ri_retail", "ri_markon",
                    "var_qty", "var_cost", "var_retail", "var_markon"
                ]

                for i in range(12):
                    current[keys[i]] = fix_num(nums[i])

    return items


# =========================
# RUN APP
# =========================
if st.button("Run Parse"):

    if txt:

        data = parse(txt)
        df = pd.DataFrame(data)

        st.subheader("📦 Raw Data")
        st.dataframe(df, use_container_width=True)

        # =========================
        # KPI SUMMARY
        # =========================
        st.subheader("📊 KPI Summary")

        col1, col2, col3 = st.columns(3)

        col1.metric("Total SKUs", len(df))

        var_qty = df["var_qty"].sum() if "var_qty" in df else 0
        col2.metric("Total Variance Qty", var_qty)

        loss_rows = df[df.get("var_qty", 0) != 0]
        col3.metric("Variance Items", len(loss_rows))


        # =========================
        # VARIANCE TABLE
        # =========================
        st.subheader("⚠️ Variance Only")
        st.dataframe(loss_rows, use_container_width=True)


        # =========================
        # DOWNLOAD EXCEL
        # =========================
        output = BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Raw Data")
            loss_rows.to_excel(writer, index=False, sheet_name="Variance")

        output.seek(0)

        st.download_button(
            "⬇️ Download Excel Report",
            output,
            file_name="stocktake_report.xlsx"
        )

    else:
        st.warning("Please upload file or paste URL first")
