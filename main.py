from collections import defaultdict

import pandas as pd
import streamlit as st

import parsers

# Title of the app
st.title("Memory Report Visualization")

# File uploader widget
uploaded_file = st.file_uploader("Choose a file", type=["txt", "memreport"])

fulldoc: list[str] = []
if uploaded_file is not None:
    # Read the uploaded file
    fulldoc = uploaded_file.read().decode("utf-8").splitlines()

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

    # Iterate through each category
    for category, data in report_categories.items():
        if "class=" in category:
            class_name = category.replace("class=", "")
            st.header(f"Category: {class_name}")
            f_result, summary = parsers.class_parser(data, category)
            df = pd.DataFrame(f_result)

            # Convert NumKB to numeric values for comparison
            df["NumKB"] = pd.to_numeric(df["NumKB"], errors='coerce')

            # Create an interactive slider to filter data
            max_mb = st.slider(f"MB Ceiling for {class_name}", min_value=0, max_value=250, value=100, key=class_name)
            filtered_df = df[df["NumKB"] <= max_mb]

            # Custom function to highlight high values
            def highlight_high_values(val):
                color = "yellow" if isinstance(val, (int, float)) and val > max_mb else ""
                return f"background-color: {color}"

            styled_df = filtered_df.style.applymap(highlight_high_values)
            st.dataframe(styled_df)

            # Create a bar chart
            st.write("### Bar Chart")
            st.bar_chart(df.set_index("Object")["NumKB"])

            # Display the filtered dataframe
            st.write("### Filtered Data", filtered_df)

            # Create a bar chart for the filtered data
            st.write("### Filtered Bar Chart")
            st.bar_chart(filtered_df.set_index("Object")["NumKB"])

        if category == "ListTextures":
            st.header("Category: ListTextures")
            texture_data, texture_summary = parsers.list_texture_parser(report_categories["ListTextures"])
            texture_df = pd.DataFrame(texture_data)

            # Display the dataframe
            st.write("### Texture Data", texture_df)

            # Filter by VT parameter
            vt_filter = st.selectbox("Filter by VT parameter", ["All", "YES", "NO"])
            if vt_filter != "All":
                texture_df = texture_df[texture_df["VT"] == vt_filter]

            # Display the filtered dataframe
            st.write("### Filtered Texture Data", texture_df)

            # Calculate resolution and size
            def calculate_resolution(size_str):
                width_height_str = size_str.split()[0]
                width, height = width_height_str.split("x")
                return int(width.strip()) * int(height.strip())

            def calculate_size(size_str):
                return int(size_str.split("(")[1].split(" ")[0])

            texture_df["Resolution"] = texture_df["MaxAllowedSize: Width x Height (Size in KB, Authored Bias)"].apply(calculate_resolution)
            texture_df["Size (KB)"] = texture_df["Current/InMem: Width x Height (Size in KB)"].apply(calculate_size)

            # Sort by resolution and size
            sorted_by_resolution = texture_df.sort_values(by="Resolution", ascending=False)
            sorted_by_size = texture_df.sort_values(by="Size (KB)", ascending=False)

            # Display sorted dataframes
            st.write("### Textures with Biggest Resolution", sorted_by_resolution)
            st.write("### Textures with Biggest Size", sorted_by_size)

            # Create bar charts for resolution and size
            st.write("### Bar Chart for Biggest Resolution")
            st.bar_chart(sorted_by_resolution.set_index("Name")["Resolution"])

            st.write("### Bar Chart for Biggest Size")
            st.bar_chart(sorted_by_size.set_index("Name")["Size (KB)"])
