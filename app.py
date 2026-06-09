import streamlit as st
import requests
import pandas as pd
import re
from io import BytesIO

st.title("Stocktake Analytics App")

url = st.text_input("Paste GitHub TXT URL")

def fix_num(x):
    if x.endswith("-"):
        return -float(x.replace("-", ""))
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

        # SKU detect
        m = re.match(r'^(\d+)\s+(.+?)\s{2,}(.+?)\s+(\d{6,})\s+(.*)$', line)

        if m:
            current = {
                "dept": m.group(1),
                "brand": m.group(3),
                "sku": m.group(4),
                "desc": m.group(5)
            }
            items.append(current)

        if "Outright:" in line and current:
            nums = re.findall(r'[\d\.\-]+', line)

            if len(nums) >= 10:
                current["actual_qty"] = fix_num(nums[0])
                current["actual_cost"] = fix_num(nums[1])
                current["actual_retail"] = fix_num(nums[2])
                current["ri_qty"] = fix_num(nums[4])
                current["ri_cost"] = fix_num(nums[5])
                current["ri_retail"] = fix_num(nums[6])
                current["var_qty"] = fix_num(nums[8])
                current["var_cost"] = fix_num(nums[9])

    return items


if st.button("Run Parse"):

    if url:
        txt = requests.get(url).text
        data = parse(txt)

        df = pd.DataFrame(data)

        st.subheader("Raw Data")
        st.dataframe(df)

        # Variance only
        st.subheader("Variance Only")
        st.dataframe(df[df["var_qty"] != 0])

        # Excel download
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Raw Data")
            df[df["var_qty"] != 0].to_excel(writer, index=False, sheet_name="Variance")

        st.download_button(
            "Download Excel",
            output.getvalue(),
            file_name="stocktake.xlsx"
        )