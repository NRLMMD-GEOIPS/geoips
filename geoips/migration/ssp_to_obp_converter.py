"""Convert SSP shell scripts to Order-Based Processing (OBP) YAML workflow files."""

from pathlib import Path

import json
import re

# INPUT_DIR = Path.cwd()
INPUT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = INPUT_DIR.parent / "yaml"

OUTPUT_DIR.mkdir(exist_ok=True)


def write_top_level_content(file: Path) -> None:
    """Write the license header and status comments to the top of the file."""
    file.write_text(
        "# # # This source code is subject to the license referenced at\n"
        "# # # https://github.com/NRLMMD-GEOIPS.\n\n"
        "# script migration = done\n"
        "# product testing = ongoing\n\n"
        # "# Default values - if you do not have this exact test case available,
        # call with available data files / sectors.\n"
        # '# This exact test case required for valid comparisons \n\n'
    )


def write_workflow_top_level(file: Path) -> None:
    """Write the top-level workflow YAML metadata block."""
    with file.open("a") as fp:
        fp.write(
            "apiVersion: geoips/v1\n"
            "interface: workflows\n"
            "family: order_based\n"
            f"name: {file.stem}\n"
            "docstring: ADD THIS.\n"
            "package: geoips\n"
        )


def parse_file_lines(ssp_script: Path) -> tuple[str | None, str | None]:
    """Search for the data files."""
    content = ssp_script.read_text()
    input_file = re.search(r"\$GEOIPS_TESTDATA_DIR[^\s\\]+", content)
    return input_file.group() if input_file else None


def write_test_section(
    yaml_file: Path, input_file: str | None, compare_path: str | None = None
) -> None:
    """Write the test section with input filenames and optional compare path."""
    with yaml_file.open("a") as f:
        f.write("test:\n")
        if input_file:
            formatted_fnames = input_file.replace(
                "$GEOIPS_TESTDATA_DIR", "${GEOIPS_TESTDATA_DIR}"
            )
            f.write(f"  fnames: !ENV {formatted_fnames}\n")
        if compare_path:
            formatted_compare = compare_path.replace(
                "$GEOIPS_PACKAGES_DIR", "${GEOIPS_PACKAGES_DIR}"
            ).strip('"')
            f.write("  outputs:\n")
            f.write("    output_formatter:\n")
            f.write("      full_test_policy: on_token_mismatch # always | never\n")
            f.write(f"      compare_path: !ENV {formatted_compare}\n")
            f.write("      output_checker_name: ADD THIS\n")


def parse_sector_list(sh_file: Path) -> str | None:
    """Extract the sector list argument from the shell script."""
    content = sh_file.read_text()
    match = re.search(r"--sector_list\s+(\S+)", content)
    return match.group(1) if match else None


def parse_product_name(sh_file: Path) -> str | None:
    """Extract the product name argument from the shell script."""
    content = sh_file.read_text()
    match = re.search(r"--product_name\s+(\S+)", content)
    return match.group(1) if match else None


def parse_minimum_coverage(sh_file: Path) -> float | None:
    """Extract the minimum coverage threshold from the shell script."""
    content = sh_file.read_text()
    match = re.search(r"--minimum_coverage\s+(\S+)", content)
    return match.group(1) if match else None


def write_global_arguments(
    yaml_file: Path,
    sector_list: str | None,
    product_name: str | None,
    minimum_coverage: float | None,
) -> None:
    """Write the globals section with product name, sector list, and coverage."""
    with yaml_file.open("a") as f:
        f.write("  globals:\n")
        # f.write("    product_db: False\n")
        # f.write("    product_db_writer: None\n")
        # f.write("    product_db_writer_kwargs: None\n")
        if product_name:
            f.write(f"    product_name: {product_name}\n")
        else:
            f.write("    product_name: None\n")
        f.write("    reader_defined_area_def: False\n")
        # f.write("    window_start_time: None\n")
        # f.write("    window_end_time: None\n")
        if sector_list:
            f.write(f'    # sector_list: ["{sector_list}"]\n')
        # No need to write if the value is None
        # else:
        #     f.write("    sector_list: None\n")
        # do not optimize to if minimum_coverage: as it would skip falsy values
        # such as 0
        if minimum_coverage is not None:
            f.write(f"    minimum_coverage: {minimum_coverage} \n")


def parse_reader(sh_file: Path):
    """Extract reader name and all related arguments from the shell script."""
    content = sh_file.read_text()
    match = re.search(r"--reader_name\s+(\S+)", content)
    reader_name = match.group(1) if match else None
    resampled_read = bool(re.search(r"--resampled_read", content))
    match_self_register_dataset = re.search(
        r"--self_register_dataset\s+['\"]?([^'\"]+)['\"]?",
        content,
    )
    self_register_dataset = (
        match_self_register_dataset.group(1) if match_self_register_dataset else None
    )
    match_self_register_source = re.search(
        r"--self_register_source\s+['\"]?([^'\"]+)['\"]?", content
    )
    self_register_source = (
        match_self_register_source.group(1) if match_self_register_source else None
    )

    match_no_pre_sectoring = re.search(r"--no-presectoring", content)
    presector = False if match_no_pre_sectoring else None

    reader_kwargs = {}
    kwargs_match = re.search(r"--reader_kwargs\s+'({.*?})'", content)
    if kwargs_match:
        reader_kwargs = json.loads(kwargs_match.group(1))
    return (
        reader_name,
        resampled_read,
        self_register_dataset,
        self_register_source,
        reader_kwargs,
        presector,
    )


# write_reader(yaml_file, reader_name, resampled_read, self_register_dataset,
# self_register_source, presector, reader_kwargs)


def write_sector(yaml_file: Path, sector_list: str | None) -> None:
    """Write the sector step block to the YAML workflow file."""
    if not sector_list:
        return
    with yaml_file.open("a") as f:
        f.write("    sector:\n")
        f.write("      kind: sector\n")
        f.write(f"      name: {sector_list}\n")
        f.write("      depends_on: []\n")


def write_reader(
    yaml_file: Path,
    reader_name: str | None,
    resampled_read: bool,
    self_register_dataset: str | None,
    self_register_source: str | None,
    presector: bool | None,
    reader_kwargs: dict,
) -> None:
    """Write the reader step block including optional reader arguments."""
    if not reader_name:
        return

    with yaml_file.open("a") as f:
        f.write("    reader:\n")
        f.write("      kind: reader\n")
        f.write(f"      name: {reader_name}\n")
        args = {}
        if resampled_read:
            args["resampled_read"] = True
        if presector is not None:
            args["presector"] = presector
        if self_register_dataset:
            args["self_register_dataset"] = self_register_dataset
        if self_register_source:
            args["self_register_source"] = self_register_source
        args.update(reader_kwargs)
        if args:
            f.write("      arguments: \n")
            for key, value in args.items():
                f.write(f"        {key}: {value}\n")
        f.write("      depends_on: [sector]\n")


def parse_product(sh_file: Path) -> str | None:
    """Extract the product name from the shell script."""
    content = sh_file.read_text()
    match = re.search(r"--product_name\s+(\S+)", content)
    return match.group(1) if match else None


def write_product(yaml_file: Path, product_name: str | None) -> None:
    """Write the product step block to the YAML workflow file."""
    if not product_name:
        return
    source_name = yaml_file.stem.split("_")[0]
    with yaml_file.open("a") as f:
        f.write(f"    {source_name}_{product_name}:\n")
        f.write("      kind: product\n")
        f.write(f"      name: [{source_name}, {product_name}]\n")
        f.write("      arguments: {}\n")
        f.write("      depends_on: [sector, reader]\n")


def parse_output_checker(sh_file: Path) -> str | None:
    """Extract the compare path for output checking from the shell script."""
    content = sh_file.read_text()
    match = re.search(
        r'--compare_path\s+["\']?([^"\']+)["\']?',
        content,
    )
    return match.group(1) if match else None


# def write_output_chekcer(yaml_file: Path, output_checker: str | None) -> None:
#     if not output_checker:
#         return
#     with yaml_file.open("a") as f:
#         f.write("    output_checker:\n")
#         f.write("      kind: output_checker\n")
#         f.write(f"      name: PLUGIN_PROVIDED\n")
#         args = {}
#         # f.write(f"      arguments: {output_checker}\n")
#         args["compare_path"] = output_checker
#         if args:
#             f.write("      arguments: {\n")
#         for key, value in args.items():
#             f.write(f"        {key}: !ENV {value}\n")
#             f.write("      }\n")


def parse_output_formatter(sh_file: Path) -> str | None:
    """Extract the output formatter name from the shell script."""
    content = sh_file.read_text()
    match = re.search(r"--output_formatter\s+(\S+)", content)
    return match.group(1) if match else None


def write_output_formatter(yaml_file: Path, output_formatter: str | None) -> None:
    """Write the output formatter step block to the YAML workflow file."""
    if not output_formatter:
        return
    with yaml_file.open("a") as f:
        f.write("    output_formatter:\n")
        f.write("      kind: output_formatter\n")
        f.write(f"      name: {output_formatter}\n")
        f.write("      arguments: {}\n")


def parse_filename_formatter(sh_file: Path) -> str | None:
    """Extract the filename formatter name from the shell script."""
    content = sh_file.read_text()
    match = re.search(r"--filename_formatter\s+(\S+)", content)
    return match.group(1) if match else None


def write_filename_formatter(
    yaml_file: Path,
    filename_formatter: str | None,
    product_step_id: str | None = None,
    has_coverage_checker: bool = False,
) -> None:
    """Write the filename formatter step block with computed dependencies."""
    if not filename_formatter:
        return
    depends_on = []
    if product_step_id:
        depends_on.append(f"{product_step_id}.algorithm")
    depends_on.append("sector")
    if has_coverage_checker:
        depends_on.append("check_coverage")
    with yaml_file.open("a") as f:
        f.write("    filename_formatter:\n")
        f.write("      kind: filename_formatter\n")
        f.write(f"      name: {filename_formatter}\n")
        f.write(f"      depends_on: [{', '.join(depends_on)}]\n")


def parse_feature_annotator(sh_file: Path) -> str | None:
    """Extract the feature annotator name from the shell script."""
    content = sh_file.read_text()
    match = re.search(r"--feature_annotator\s+(\S+)", content)
    return match.group(1) if match else None


def parse_gridline_annotator(sh_file: Path) -> str | None:
    """Extract the gridline annotator name from the shell script."""
    content = sh_file.read_text()
    match = re.search(r"--gridline_annotator\s+(\S+)", content)
    return match.group(1) if match else None


def write_feature_annotator(yaml_file: Path, feature_annotator: str | None) -> None:
    """Write the feature annotator step block to the YAML workflow file."""
    if not feature_annotator:
        return
    with yaml_file.open("a") as f:
        f.write("    feature_annotator:\n")
        f.write("      kind: feature_annotator\n")
        f.write(f"      name: {feature_annotator}\n")
        f.write("      arguments: {}\n")


def write_gridline_annotator(yaml_file: Path, gridline_annotator: str | None) -> None:
    """Write the gridline annotator step block to the YAML workflow file."""
    if not gridline_annotator:
        return
    with yaml_file.open("a") as f:
        f.write("    gridline_annotator:\n")
        f.write("      kind: gridline_annotator\n")
        f.write(f"      name: {gridline_annotator}\n")
        f.write("      arguments: {}\n")


if __name__ == "__main__":
    for file in INPUT_DIR.glob("*.sh"):
        if "config" not in file.name:
            # yaml_file = OUTPUT_DIR / (file.stem + ".yaml")
            # yaml_file.touch()
            yaml_file = OUTPUT_DIR / (
                file.stem.replace(".", "_").replace("-", "_").lower() + ".yaml"
            )

            write_top_level_content(yaml_file)

            write_workflow_top_level(yaml_file)

            # input_file_lines, logging_level = write_test_function(file)
            input_file_lines = parse_file_lines(file)
            compare_path = parse_output_checker(file)
            write_test_section(yaml_file, input_file_lines, compare_path)
            with yaml_file.open("a") as fp:
                fp.write("spec:\n")

            sector_list = parse_sector_list(file)
            product_name = parse_product_name(file)
            minimum_coverage = parse_minimum_coverage(file)
            write_global_arguments(
                yaml_file, sector_list, product_name, minimum_coverage
            )

            with yaml_file.open("a") as fp:
                fp.write("  steps:\n")

            write_sector(yaml_file, sector_list)

            (
                reader_name,
                resampled_read,
                self_register_dataset,
                self_register_source,
                reader_kwargs,
                presector,
            ) = parse_reader(file)
            write_reader(
                yaml_file,
                reader_name,
                resampled_read,
                self_register_dataset,
                self_register_source,
                presector,
                reader_kwargs,
            )

            product_step = parse_product(file)
            write_product(yaml_file, product_step)

            filename_formatter_step = parse_filename_formatter(file)
            source_name = yaml_file.stem.split("_")[0]
            product_step_id = f"{source_name}_{product_step}" if product_step else None
            write_filename_formatter(
                yaml_file,
                filename_formatter_step,
                product_step_id=product_step_id,
                has_coverage_checker=minimum_coverage is not None,
            )

            feature_annotator = parse_feature_annotator(file)
            write_feature_annotator(yaml_file, feature_annotator)

            gridline_annotator = parse_gridline_annotator(file)
            write_gridline_annotator(yaml_file, gridline_annotator)

            output_formatter_step = parse_output_formatter(file)
            write_output_formatter(yaml_file, output_formatter_step)
            # output_checker = parse_output_checker(file)
            # write_output_chekcer(yaml_file, output_checker)
