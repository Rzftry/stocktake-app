import streamlit as st
import requests
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Stocktake Analytics", layout="wide")

st.title("📊 Stocktake Analytics App")

url = st.text_input("Paste GitHub RAW TXT URL")


def parse(txt):

    lines = txt.split("\n")

    data = []
    current = None

    for line in lines:
        line = line.strip()

        if not line:
            continue

        # skip headers / noise
        if any(x in line.upper() for x in [
            "DEPT", "BRAND", "SHORT SKU", "ACTUAL STOCK",
            "VARIANCE", "MARK ON%", "REPORT CODE",
            "PRINTED BY", "STORE", "SELECTION"
        ]):
            continue

        if "<----" in line or "---->" in line or "-----" in line:
            continue

        # detect SKU row
        import re
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

        # detect value row
        if "Outright:" in line and current:

            nums = re.findall(r'[\d\.\-]+', line)

            def safe_float(x):
    try:
        x = str(x).strip()
        if not x:
            return 0
        if x.endswith("-"):
            return -float(x.replace("-", ""))
        return float(x)
    except:
        return 0


def get(i):
    return safe_float(nums[i]) if len(nums) > i else 0

            if len(nums) >= 8:

                current.update({
                    "actual_qty": get(0),
                    "actual_cost": get(1),
                    "actual_retail": get(2),
                    "actual_markon": get(3),

                    "ri_qty": get(4),
                    "ri_cost": get(5),
                    "ri_retail": get(6),
                    "ri_markon": get(7),

                    "var_qty": get(8),
                    "var_cost": get(9),
                    "var_retail": get(10),
                    "var_markon": get(11),
                })

    return data


if st.button("Run Parse"):

    if not url:
        st.warning("Please paste TXT URL")
        st.stop()

    txt = requests.get(url).text
    data = parse(txt)

    df = pd.DataFrame(data)

    st.subheader("Raw Data")
    st.dataframe(df, use_container_width=True)

    st.subheader("Variance Only")
    st.dataframe(df[df["var_qty"] != 0])

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Raw Data")
        df[df["var_qty"] != 0].to_excel(writer, index=False, sheet_name="Variance")

    st.download_button(
        "Download Excel",
        output.getvalue(),
        file_name="stocktake.xlsx"
    )
