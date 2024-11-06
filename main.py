import pandas as pd
import streamlit as st
from streamlit_elements import elements, mui, nivo

import parsers

st.set_page_config(layout="wide")
pd.set_option("styler.render.max_elements", 999_999_999_999)

# Title of the app
st.title("Memory Report Visualization")


def update_session_state():
    # Delete all the items in Session state
    for key in st.session_state.keys():
        del st.session_state[key]


# Function to extract size in KB from the string
def extract_size_kb(value):
    return int(value.split("(")[1].split(" ")[0].replace("KB", "").strip())


# Function to extract resolution from the string
def extract_resolution(value):
    return tuple(map(int, value.split(" ")[0].split("x")))


legend = """
Class columns.
MaxMB: The maximum memory usage recorded for the object in megabytes.
NumMB: The current memory usage of the object in megabytes.
ResExcMB: The memory usage excluding any shared resources in megabytes.
ResExcDedSysMB: The memory usage excluding dedicated system resources in megabytes.
ResExcDedVidMB: The memory usage excluding dedicated video resources in megabytes.
ResExcUnkMB: The memory usage excluding unknown resources in megabytes.

For class total.
Max: The maximum memory usage recorded in megabytes (MB).
Res: The memory usage excluding any shared resources in megabytes (MB).
ResDedSys: The memory usage excluding dedicated system resources in megabytes (MB).
ResDedVid: The memory usage excluding dedicated video resources in megabytes (MB).
ResUnknown: The memory usage excluding unknown resources in megabytes (MB).
"""

with st.expander("See memreport legend"):
    st.code(legend, language="markdown")

# File uploader widget
uploaded_file = st.file_uploader("Choose a file", type=["txt", "memreport"], on_change=update_session_state)


# Custom function to highlight high values
def highlight_high_values(val, threshold):
    color = "orange" if isinstance(val, (int, float)) and val > threshold else ""
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
                st.write(st.session_state[class_name]["ResExcMB"].sum())
                # Create an interactive input to filter data
                max_mb = st.number_input("Size threshold in MB", key=category, value=5.0)

                col1, col2 = st.columns(2)
                styled_df = st.session_state[class_name].style.map(lambda x: highlight_high_values(x, max_mb))

                with col1:
                    st.dataframe(styled_df)

                with col2:
                    # Prepare data for Nivo pie chart
                    copy_df = pd.DataFrame(st.session_state[class_name][["Object", "ResExcMB"]])
                    filtered_df = copy_df[copy_df["ResExcMB"] >= max_mb]
                    if len(filtered_df) > 200:
                        st.error("You're going to visualize more than 200 elements. App will become unresponsive. Suggestion to filter assets.")
                    elif len(filtered_df) < 2:
                        st.write("Nothing to see here.")
                    else:
                        pie_data = filtered_df.rename(columns={"Object": "id", "ResExcMB": "value"})
                        pie_data["label"] = pie_data["id"]
                        pie_data = pie_data.to_dict(orient="records")
                        with elements(class_name), mui.Box(sx={"height": 600}):
                            nivo.Pie(
                                data=pie_data,
                                width=800,
                                innerRadius=0.3,
                                padAngle=0.4,
                                cornerRadius=3,
                                colors={"scheme": "nivo"},
                                borderWidth=1,
                                borderColor={"from": "color", "modifiers": [["darker", 0.2]]},
                                radialLabelsSkipAngle=10,
                                radialLabelsTextXOffset=6,
                                radialLabelsTextColor="#333333",
                                sliceLabelsSkipAngle=10,
                                sliceLabelsTextColor="#333333",
                                theme={
                                    "background": "#FFFFFF",
                                    "textColor": "#31333F",
                                    "tooltip": {
                                        "container": {
                                            "background": "#FFFFFF",
                                            "color": "#000000",
                                        }
                                    },
                                },
                            )
                st.divider()

            if category == "ListTextures" or category.__contains__("listtexture"):
                st.header("Category: ListTextures")
                if category not in st.session_state:
                    f_result, summary = parsers.list_texture_parser(st.session_state.init_data[category])
                    st.session_state[category] = f_result
                    st.session_state[f"{category}_sum"] = summary

                texture_df = pd.DataFrame(st.session_state[category])

                st.table(st.session_state[f"{category}_sum"])

                # Add columns for sorting
                st.session_state[category]["Cooked_Size_KB"] = st.session_state[category][
                    "Cooked/OnDisk: Width x Height (Size in KB, Authored Bias)"
                ].apply(extract_size_kb)
                st.session_state[category]["Cooked_Resolution"] = st.session_state[category][
                    "Cooked/OnDisk: Width x Height (Size in KB, Authored Bias)"
                ].apply(extract_resolution)
                st.session_state[category]["InMem_Size_KB"] = st.session_state[category]["Current/InMem: Width x Height (Size in KB)"].apply(
                    extract_size_kb
                )
                st.session_state[category]["InMem_Resolution"] = st.session_state[category]["Current/InMem: Width x Height (Size in KB)"].apply(
                    extract_resolution
                )

                on = st.toggle("Sort by resolution in memory")

                if on:
                    sorted = st.session_state[category].sort_values(
                        by="InMem_Resolution",
                        key=lambda x: x.map(lambda res: (int(res[0]) ** 2 + int(res[1]) ** 2) ** (1 / 2)),
                        ascending=False,
                    )
                else:
                    sorted = st.session_state[category]

                # Display the DataFrame with filters applied
                st.dataframe(sorted)
                # st.divider()

                import plotly.express as px

                df = st.session_state[category]

                # Format the name of the asset
                df["Formatted_Name"] = df["Name"].apply(lambda x: x.split("/")[-1])

                # Convert InMem_Size_KB to MB for tooltip display
                df["InMem_Size_MB"] = df["InMem_Size_KB"] / 1024

                # Create the treemap with additional information in the tooltip
                fig = px.treemap(
                    df,
                    path=["LODGroup", "Formatted_Name"],
                    values="InMem_Size_KB",
                    hover_data={
                        "Name": True,
                        "Format": True,
                        "Streaming": True,
                        "UnknownRef": True,
                        "VT": True,
                        "Usage Count": True,
                        "NumMips": True,
                        "Uncompressed": True,
                        "InMem_Size_MB": True,
                    },
                )

                fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))

                # Display the treemap in Streamlit
                st.plotly_chart(fig)
            if category == "ConfigMem":
                st.header("Category: Config cache memory usage")

                if category not in st.session_state:
                    f_result = parsers.config_mem_parser(st.session_state.init_data[category])
                    st.session_state[category] = f_result

                config_mem_df = pd.DataFrame(st.session_state[category])
                st.dataframe(config_mem_df, use_container_width=True)
            if category == "r.DumpRenderTargetPoolMemory":
                st.header("Pooled Render Targets")
                if category not in st.session_state:
                    f_result = parsers.dump_rt_parser(st.session_state.init_data[category])
                    st.session_state[category] = f_result

                rt_pool_df = pd.DataFrame(st.session_state[category]).set_index("Name")
                st.dataframe(rt_pool_df, use_container_width=True)
                import plotly.express as px

                fig = px.icicle(
                    st.session_state[category],
                    path=[px.Constant("all"), "Name", "Format", "Dimensions"],
                    values="SizeMB",
                )
                fig.update_traces(root_color="lightgrey")
                st.plotly_chart(fig)
            if category == "ListParticleSystems":
                st.header("ParticleSystems")
                if category not in st.session_state:
                    f_result = parsers.particle_system_parser(st.session_state.init_data[category])
                    st.session_state[category] = f_result
                particle_systems_df = pd.DataFrame(st.session_state[category]).set_index("Name")
                st.dataframe(particle_systems_df, use_container_width=True)
