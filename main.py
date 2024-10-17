import pandas as pd
import streamlit as st

import parsers

pd.set_option("styler.render.max_elements", 999_999_999_999)

# Title of the app
st.title("Memory Report Visualization")


def update_session_state():
    # Delete all the items in Session state
    for key in st.session_state.keys():
        del st.session_state[key]


# File uploader widget
uploaded_file = st.file_uploader("Choose a file", type=["txt", "memreport"], on_change=update_session_state)


# Custom function to highlight high values
def highlight_high_values(val, threshold):
    color = "yellow" if isinstance(val, (int, float)) and val > threshold else ""
    return f"background-color: {color}"


fulldoc: list[str] = []
if uploaded_file is not None:
    # Read the uploaded file
    fulldoc = uploaded_file.read().decode("utf-8").splitlines()

    if "init_data" not in st.session_state:
        categories_data, report_meta = parsers.init_file(fulldoc)
        st.session_state.init_data = categories_data
        st.session_state.init_meta = report_meta

    st.table(st.session_state.init_meta)
    categories_to_parse = st.multiselect("Choose categories", st.session_state.init_data.keys())
    if not categories_to_parse:
        st.error("Please select at least one category.")
    else:
        for category in categories_to_parse:
            if "class=" in category:
                class_name = category.replace("class=", "")
                st.header(f"Category: {class_name}")
                if class_name not in st.session_state:
                    f_result, summary = parsers.class_parser(st.session_state.init_data[category], category)
                    st.session_state[class_name] = f_result
                    st.session_state[f"{class_name}_sum"] = summary

                st.table(st.session_state[f"{class_name}_sum"])

                # Create an interactive input to filter data
                max_mb = st.number_input("Size threshold in MB", key=category, value=5)

                styled_df = st.session_state[class_name].style.map(lambda x: highlight_high_values(x, max_mb))
                st.dataframe(styled_df)

    # if a:
    #     # Iterate through each category
    #     for category, data in categories_data.items():
    #         if "class=" in category:
    #             # Convert NumKB to numeric values for comparison
    #             df["NumKB"] = pd.to_numeric(df["NumKB"], errors="coerce")
    #
    #             filtered_df = df[df["NumKB"] <= max_mb]
    #
    #             # Create a bar chart
    #             st.write("### Bar Chart")
    #             st.bar_chart(df.set_index("Object")["NumKB"])
    #
    #             # Display the filtered dataframe
    #             st.write("### Filtered Data", filtered_df)
    #
    #             # Create a bar chart for the filtered data
    #             st.write("### Filtered Bar Chart")
    #             st.bar_chart(filtered_df.set_index("Object")["NumKB"])
    #
    #         if category == "ListTextures":
    #             st.header("Category: ListTextures")
    #             texture_data, texture_summary = parsers.list_texture_parser(data)
    #             texture_df = pd.DataFrame(texture_data)
    #
    #             # Display the dataframe
    #             st.write("### Texture Data", texture_df)
    #
    #             # Filter by VT parameter
    #             vt_filter = st.selectbox("Filter by VT parameter", ["All", "YES", "NO"])
    #             if vt_filter != "All":
    #                 texture_df = texture_df[texture_df["VT"] == vt_filter]
    #
    #             # Display the filtered dataframe
    #             st.write("### Filtered Texture Data", texture_df)
    #
    #             # Calculate resolution and size
    #             def calculate_resolution(size_str):
    #                 width_height_str = size_str.split()[0]
    #                 width, height = width_height_str.split("x")
    #                 return int(width.strip()) * int(height.strip())
    #
    #             def calculate_size(size_str):
    #                 return int(size_str.split("(")[1].split(" ")[0])
    #
    #             print(texture_df.keys())
    #             try:
    #                 texture_df["Resolution"] = texture_df["MaxAllowedSize: Width x Height (Size in KB, Authored Bias)"].apply(calculate_resolution)
    #             except KeyError:
    #                 texture_df["Resolution"] = texture_df["Cooked/OnDisk: Width x Height (Size in KB, Authored Bias)"].apply(calculate_resolution)
    #             texture_df["Size (KB)"] = texture_df["Current/InMem: Width x Height (Size in KB)"].apply(calculate_size)
    #
    #             # Sort by resolution and size
    #             sorted_by_resolution = texture_df.sort_values(by="Resolution", ascending=False)
    #             sorted_by_size = texture_df.sort_values(by="Size (KB)", ascending=False)
    #
    #             # Display sorted dataframes
    #             st.write("### Textures with Biggest Resolution", sorted_by_resolution)
    #             st.write("### Textures with Biggest Size", sorted_by_size)
    #
    #             # Create bar charts for resolution and size
    #             st.write("### Bar Chart for Biggest Resolution")
    #             st.bar_chart(sorted_by_resolution.set_index("Name")["Resolution"])
    #
    #             st.write("### Bar Chart for Biggest Size")
    #             st.bar_chart(sorted_by_size.set_index("Name")["Size (KB)"])
