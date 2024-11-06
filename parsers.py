from collections import defaultdict
from pathlib import Path

import pandas as pd
import streamlit as st


@st.cache_data
def init_file(document_lines: list[str]) -> tuple[dict[str, list[str]], dict[str, str]]:
    """Doing the initial parse to get data by category"""
    if not document_lines:
        raise ImportError("No data from file provided!")

    report_meta: dict = defaultdict(str)

    # getting the metadata of the report
    for mi_line in document_lines[:7]:
        try:
            meta_key, value = mi_line.split(":")
            report_meta[meta_key] = value.strip()
        except ValueError:
            print("Couldn't parse metadata of the report.")
            print(f"Line failed: {mi_line}")

    report_categories: dict = defaultdict(list)
    report_data: bool = False
    category_name: str = ""

    for line in document_lines[7:]:
        if line.strip() == "":
            continue

        command_start = line.startswith("MemReport: Begin command")

        if line.startswith("MemReport: End command"):
            report_data = False
            continue

        if report_data:
            report_categories[category_name].append(line)
            continue

        if command_start:
            category_name = line.split('"')[1].replace('"', "")

            if category_name.find("class=") != -1:
                category_name = category_name.split("class=")[1].split(" ")[0]
                category_name = f"class={category_name}"

            if category_name.find("-alphasort") != -1:
                category_name = category_name.replace("-alphasort", "")

            category_name = category_name.strip()
            report_data = True
            continue

    return report_categories, report_meta


def particle_mem_parser():
    """Parser for DumpParticleMem"""


@st.cache_data
def config_mem_parser(data: list[str]) -> pd.DataFrame:
    """Parser for ConfigMem"""
    formatted_data: dict = {"FileName": [], "NumMegaBytes": [], "MaxMegaBytes": []}

    for line in data[3:-1]:
        columns = " ".join(line.split()).split()
        formatted_data["FileName"].append(columns[0])
        formatted_data["NumMegaBytes"].append(float(columns[1]) / 1048576)
        formatted_data["MaxMegaBytes"].append(float(columns[2]) / 1048576)

    data_df = pd.DataFrame.from_dict(formatted_data)
    return data_df


@st.cache_data
def dump_rt_parser(data: list[str]) -> pd.DataFrame:
    """Parser for r.DumpRenderTargetPoolMemory"""
    import re

    # Regular expression to parse the data lines
    pattern = re.compile(r"\s*(\d+\.\d+MB)\s+(\d+x\s*\d+(?:x\s*\d+)?)\s+(\dmip\(s\))\s+([^\(]+)\s+\(([^)]+)\)\s+(Unused frames:\s*\d+)")

    # Initialize the data dictionary
    data_dict = {"Name": [], "SizeMB": [], "Dimensions": [], "Mips": [], "Format": [], "Unused Frames": []}

    # Process each line
    for line in data[1:-3]:
        match = pattern.match(line)
        if match:
            size = match.group(1).replace("MB", "")
            dimensions = match.group(2).replace(" ", "").split("x")
            mips = match.group(3)
            name = match.group(4).strip()
            format_ = match.group(5)
            unused_frames = match.group(6)

            data_dict["Name"].append(name)
            data_dict["SizeMB"].append(float(size))
            data_dict["Dimensions"].append((dimensions[0], dimensions[1]))
            data_dict["Mips"].append(mips)
            data_dict["Format"].append(format_)
            data_dict["Unused Frames"].append(unused_frames)

    df_data = pd.DataFrame.from_dict(data_dict)
    return df_data


@st.cache_data
def list_texture_parser(data: list[str]) -> tuple[pd.DataFrame, dict]:
    """Parser for ListTextures"""
    import re

    in_data: list[str] = data[2:-14]
    columns_raw: str = data[1]
    columns: list[str] = []

    formatted_output: dict = defaultdict(list)

    # Regular expression to match the first two columns and then split by commas
    if columns_raw.find("MaxAllowedSize:") != -1:
        pattern = r"(MaxAllowedSize: Width x Height \(Size in KB, Authored Bias\)), (Current/InMem: Width x Height \(Size in KB\)), (.*)"
    elif columns_raw.find("Cooked/OnDisk:") != -1:
        pattern = r"(Cooked/OnDisk: Width x Height \(Size in KB, Authored Bias\)), (Current/InMem: Width x Height \(Size in KB\)), (.*)"
    else:
        raise ValueError("There's no pattern to match for texture parser!")

    # Use re.match to apply the pattern
    match = re.match(pattern, columns_raw)
    if match:
        # Extract the first two columns and the rest
        columns = [match.group(1), match.group(2)] + match.group(3).split(", ")

    for line in in_data:
        if line.startswith("Total "):
            continue
        pattern = re.compile(r",\s*(?![^()]*\))")
        data_values = pattern.split(line)

        # Append each value to the corresponding column list
        for column, value in zip(columns, data_values):
            formatted_output[column].append(value.strip())

    # Pattern for summary
    pattern = re.compile(r"Total (.+?) size: InMem= ([\d.]+ MB)  OnDisk= ([\d.]+ MB)(?:  Count=(\d+), CountApplicableToMin=(\d+))?")

    # Initialize the summary dictionary
    summary_lines = data[-14:]
    summary = {}

    # Process each line
    for line in summary_lines:
        match = pattern.match(line)
        if match:
            key = match.group(1)
            in_mem = match.group(2)
            on_disk = match.group(3)
            count = match.group(4)
            count_applicable_to_min = match.group(5)

            summary[key] = {"InMem": in_mem, "OnDisk": on_disk, "Count": count, "CountApplicableToMin": count_applicable_to_min}

    data_df = pd.DataFrame.from_dict(formatted_output)
    return data_df, summary


def particle_system_parser():
    """Parser for ListParticleSystems"""


@st.cache_data
def class_parser(data: list[str], class_name: str) -> tuple[pd.DataFrame, dict]:
    """Parser for various Classes"""
    import math

    pure_class_name: str = class_name.replace("class=", "")
    formated_data: dict[str, list[str | float]] = defaultdict(list)
    class_summary: dict[str, float] = {}

    columns: list[str] = []
    is_data = False
    for line in data[2:-1]:
        if pure_class_name in line:
            # line = line.replace(pure_class_name, "")
            is_data = True
        else:
            is_data = False
            if "Class" in line and "Count" in line:
                break

        if not is_data:
            if columns.__len__() == 0:
                columns = line.split()
            continue
        else:
            asset_data = line.split()[1:]
            for i, col in enumerate(columns):
                value = float(asset_data[i]) / 1000 if col != "Object" else asset_data[i]
                if isinstance(value, float):
                    value = math.ceil(value * 100) / 100

                if col == "Object":
                    value = Path(value).name

                if col.__contains__("KB"):
                    col = col.replace("KB", "MB")

                formated_data[col].append(value)

    # building summary for the class
    summary = data[-1].split()
    class_summary["Objects"] = int(summary[0])
    for entry in data[-1].split("(")[1].split("/"):
        ln = entry.split(":")
        name = ln[0].strip()
        value = ln[1].strip()
        if "|" in value:
            ln2 = value.split("|")[1].split(":")
            value = value.split("|")[0].strip()
            name2 = ln2[0].strip()
            class_summary[name2] = float(ln[-1].strip().replace("M", ""))

        value = value.replace("M", "")
        value = value.replace(")", "")

        class_summary[name] = float(value)

    data_df = pd.DataFrame.from_dict(formated_data)
    return data_df, class_summary
