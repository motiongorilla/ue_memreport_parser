from collections import defaultdict

import pandas as pd
import streamlit as st

import parsers

file = "memreport_example.memreport"
fulldoc: list[str] = []

with open(file) as f:
    fulldoc = f.readlines()

report_meta: dict = defaultdict(str)
report_categories: dict = defaultdict(list)

# getting lines by categories and metadata of the report
report_command: bool = False
category_name: str = ""
for line in fulldoc:
    if line.strip() == "":
        continue

    command_start = line.startswith("MemReport:")
    if not report_command and not command_start:
        # getting the metadata of the report
        meta_key, value = line.split(":")
        report_meta[meta_key] = value.strip()
        continue

    if command_start:
        if line.find(category_name):
            command_start = False
            report_command = False

        category_name = line.split('"')[1].replace('"', "")
        if category_name.find("-alphasort") != -1:
            category_name = category_name.replace("-alphasort", "")

        if category_name.find("class=") != -1:
            category_name = category_name.split("class=")[1].split(" ")[0]
            category_name = f"class={category_name}"

        report_command = report_command is not True
        continue

    if report_command:
        report_categories[category_name].append(line)

# for category, data in report_categories.items():
# if "class=" in category:
#     print(f"==========={category}")
#     f_result, summary = parsers.class_parser(data, category)
#     print(f_result)
# if category == "ListTextures":
#     parsers.list_texture_parser(data)
# if category == "r.DumpRenderTargetPoolMemory":
#     print(parsers.dump_rt_parser(data))
# cat_data = report_categories["class=StaticMesh"]
# f_result, summary = parsers.class_parser(cat_data, "class=StaticMesh")
#
# Title of the app
st.title("Memory Report Visualization")

# Iterate through each category
for category, data in report_categories.items():
    if "class=" in category:
        st.header(f"Category: {category}")
        f_result, summary = parsers.class_parser(data, category)
        df = pd.DataFrame(f_result)

        # Create a bar chart
        st.write("### Bar Chart")
        st.bar_chart(df.set_index("Object")["NumKB"])

        # Create a heatmap-like table
        st.write("### Heatmap-like Table")
        st.dataframe(df.style.background_gradient(cmap="viridis"))

        # Create an interactive slider to filter data
        max_mb = st.slider(f"MB Ceiling for {category}", min_value=0, max_value=1024, value=100, key=category)
        filtered_df = df[df["NumKB"] <= max_mb]

        # Display the filtered dataframe
        st.write("### Filtered Data", filtered_df)

        # Create a bar chart for the filtered data
        st.write("### Filtered Bar Chart")
        st.bar_chart(filtered_df.set_index("Object")["NumKB"])
