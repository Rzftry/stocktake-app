import streamlit as st
import requests
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Stocktake Analytics", layout="wide")

st.title("📊 Stocktake Analytics App")

url = st.text_input("Paste GitHub RAW TXT URL")


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


def get(nums, i):
    return safe_float(nums[i]) if len(nums) > i else 0


def parse(txt):

    lines = txt.split("\n")

    data = []
    current = None

    for line in lines:
        line = line.rstrip()

        if not line:
            continue

        # detect product row (SKU row)
        if re.match(r'^\s*\d+\s{2,}', line) and "Outright:" not in line:

            parts = re.split(r'\s{2,}', line.strip())

            if len(parts) >= 4:
                try:
                    current = {
                        "dept": parts[0],
                        "department": parts[1],
                        "brand": parts[2],
                        "sku_desc": parts[3]
                    }
                    data.append(current)
                except:
                    pass

            continue

        # detect Outright row
        if "Outright:" in line and current:

            nums = re.findall(r'-?\d+\.?\d*', line)

            def safe(i):
                try:
                    return float(nums[i])
                except:
                    return 0

            if len(nums) >= 8:

                current.update({
                    "actual_qty": safe(0),
                    "actual_cost": safe(1),
                    "actual_retail": safe(2),
                    "actual_markon": safe(3),

                    "ri_qty": safe(4),
                    "ri_cost": safe(5),
                    "ri_retail": safe(6),
                    "ri_markon": safe(7),

                    "var_qty": safe(8),
                    "var_cost": safe(9),
                    "var_retail": safe(10),
                    "var_markon": safe(11),
                })

    return data


if st.button("Run Parse"):

    if not url:
        st.warning("Please paste TXT URL")
        st.stop()

    txt = requests.get(url).text
    data = parse(txt)

    df = pd.DataFrame(data)

    st.subheader("📄 Raw Data")
    st.dataframe(df, use_container_width=True)

    st.subheader("📉 Variance Only")
    st.dataframe(df[df["var_qty"] != 0])

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Raw Data")
        df[df["var_qty"] != 0].to_excel(writer, index=False, sheet_name="Variance")

    st.download_button(
        "⬇ Download Excel",
        output.getvalue(),
        file_name="stocktake.xlsx"
    )
