#!/usr/bin/env python3
"""
Generate VHDL code for CustomInst applications using BasicAppDataTypes v2.0.

This generator creates VHDL shim and main templates from YAML specifications
using the BasicAppDataTypes system with automatic register packing.

Features:
- Platform-aware code generation (Moku:Go/Lab/Pro/Delta)
- Automatic register packing via BADRegisterMapper
- Type-safe signal extraction using frozen VHDL packages
- Jinja2 templating for VHDL generation

Usage:
    python tools/generate_custom_inst_v2.py <yaml_file> [--output-dir OUTPUT_DIR]

Example:
    python tools/generate_custom_inst_v2.py examples/DS1140_PD_interface.yaml

Version: 2.0 (BasicAppDataTypes only, no legacy v1.0 support)
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import yaml
from jinja2 import Template, Environment, FileSystemLoader

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from forge_codegen.basic_serialized_datatypes import (
    BasicAppDataTypes,
    TYPE_REGISTRY,
    RegisterMapper,
)
from forge_codegen.models.package import BasicAppsRegPackage, DataTypeSpec

# Platform specifications
PLATFORM_MAP = {
    'moku_go': {
        'name': 'Moku:Go',
        'clock_mhz': 125,
        'slots': 2,
    },
    'moku_lab': {
        'name': 'Moku:Lab',
        'clock_mhz': 500,
        'slots': 2,
    },
    'moku_pro': {
        'name': 'Moku:Pro',
        'clock_mhz': 1250,
        'slots': 4,
    },
    'moku_delta': {
        'name': 'Moku:Delta',
        'clock_mhz': 5000,
        'slots': 3,
    },
}


def load_yaml_spec(yaml_path: Path) -> Dict[str, Any]:
    """Load and parse YAML specification file."""
    with open(yaml_path, 'r') as f:
        spec = yaml.safe_load(f)

    # Validate required fields
    required_fields = ['app_name', 'datatypes']
    for field in required_fields:
        if field not in spec:
            raise ValueError(f"Missing required field in YAML: {field}")

    # Set defaults
    if 'platform' not in spec:
        spec['platform'] = 'moku_go'
        print(f"Warning: No platform specified, defaulting to moku_go")

    if 'mapping_strategy' not in spec:
        spec['mapping_strategy'] = 'best_fit'
        print(f"Warning: No mapping_strategy specified, defaulting to best_fit")

    return spec


def create_register_package(spec: Dict[str, Any]) -> BasicAppsRegPackage:
    """Create BasicAppsRegPackage from YAML specification."""

    # Convert datatypes to DataTypeSpec objects
    datatype_specs = []
    for dt_dict in spec['datatypes']:
        # Parse datatype enum
        try:
            datatype_enum = BasicAppDataTypes[dt_dict['datatype'].upper()]
        except KeyError:
            raise ValueError(f"Unknown datatype: {dt_dict['datatype']}")

        # Get metadata
        metadata = TYPE_REGISTRY[datatype_enum]

        # Create spec
        datatype_spec = DataTypeSpec(
            name=dt_dict['name'],
            datatype=datatype_enum,
            description=dt_dict.get('description', ''),
            default_value=dt_dict.get('default_value', metadata.default_value),
            min_value=dt_dict.get('min_value', metadata.min_value),
            max_value=dt_dict.get('max_value', metadata.max_value),
            display_name=dt_dict.get('display_name', dt_dict['name']),
            units=dt_dict.get('units', metadata.unit),
        )
        datatype_specs.append(datatype_spec)

    # Create package
    package = BasicAppsRegPackage(
        app_name=spec['app_name'],
        description=spec.get('description', ''),
        datatypes=datatype_specs,
        mapping_strategy=spec['mapping_strategy'],
        platform=spec['platform'],
    )

    return package


def prepare_template_context(
    package: BasicAppsRegPackage,
    yaml_path: Path,
    platform_info: Dict[str, Any]
) -> Dict[str, Any]:
    """Prepare context dictionary for Jinja2 template rendering."""

    # Perform register mapping
    mapper = RegisterMapper()
    items = [(dt.name, dt.datatype) for dt in package.datatypes]
    mappings_list = mapper.map(items, strategy=package.mapping_strategy)

    # Determine which type packages are needed
    has_voltage = any(TYPE_REGISTRY[dt.datatype].unit == 'mV' for dt in package.datatypes)
    has_time = any(TYPE_REGISTRY[dt.datatype].unit in ('ns', 'us', 'ms', 's') for dt in package.datatypes)

    # Build signal list with all metadata needed for template
    signals = []
    for dt_spec in package.datatypes:
        metadata = TYPE_REGISTRY[dt_spec.datatype]
        type_name = dt_spec.datatype.name.lower()

        # Find register mapping for this signal
        signal_mapping = None
        for reg_map in mappings_list:
            if reg_map.name == dt_spec.name:
                signal_mapping = reg_map
                break

        if not signal_mapping:
            raise ValueError(f"No register mapping found for {dt_spec.name}")

        # Extract bit range from VHDL slice (respects RegisterMapping abstraction)
        vhdl_slice = signal_mapping.to_vhdl_slice()
        # Extract just the bit range part: "app_reg_6(31 downto 16)" -> "(31 downto 16)"
        bit_range = vhdl_slice.split('(', 1)[1].rstrip(')')
        bit_range = f"({bit_range})"

        # For single-bit signals, extract the bit position for boolean handling
        if metadata.bit_width == 1:
            bit_position = int(bit_range.strip('()'))
        else:
            bit_position = None

        # Build signal entry
        signal_info = {
            'name': dt_spec.name,
            'vhdl_type': metadata.vhdl_type,
            'vhdl_base_type': 'signed' if metadata.signedness == 'signed' else 'unsigned',
            'description': dt_spec.description,
            'default_value': dt_spec.default_value,
            'bit_width': metadata.bit_width,
            'cr_number': signal_mapping.cr_number,
            'bit_range': bit_range,
            'bit_position': bit_position,
            'is_boolean': metadata.python_type == bool,
            'is_voltage': metadata.unit == 'mV',
            'is_time': metadata.unit in ('ns', 'us', 'ms', 's'),
            'unit': metadata.unit,
            'conversion_function': type_name if metadata.unit == 'mV' else None,
            'direction': 'input',  # TODO: Add direction support in YAML
        }
        signals.append(signal_info)

    # Build register mapping summaries for comments (grouped by CR number)
    register_map_dict = {}
    for mapping in mappings_list:
        if mapping.cr_number not in register_map_dict:
            register_map_dict[mapping.cr_number] = []
        register_map_dict[mapping.cr_number].append(mapping)

    register_mappings = []
    for cr_num in sorted(register_map_dict.keys()):
        fields_list = []
        for mapping in register_map_dict[cr_num]:
            # Use RegisterMapping abstraction - extract bit range from VHDL slice
            vhdl_slice = mapping.to_vhdl_slice()
            bits_str = vhdl_slice.split('(', 1)[1].rstrip(')')
            # Convert VHDL "downto" to colon format for comments
            bits_str = bits_str.replace(' downto ', ':')

            fields_list.append({
                'name': mapping.name,
                'bits': bits_str,
                'width': mapping.bit_width(),
            })

        register_mappings.append({
            'register_index': cr_num,
            'fields': fields_list,
        })

    # Extract CR numbers used
    cr_numbers_used = sorted(set(rm['register_index'] for rm in register_mappings))

    # Calculate efficiency
    total_registers = len(register_mappings)
    total_bits_used = sum(sum(f['width'] for f in rm['fields']) for rm in register_mappings)
    total_bits_available = total_registers * 32
    efficiency_percent = round((total_bits_used / total_bits_available) * 100, 1) if total_bits_available > 0 else 0

    # Build complete context
    context = {
        'app_name': package.app_name,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'yaml_file': yaml_path.name,
        'platform_name': platform_info['name'],
        'platform_clock_mhz': platform_info['clock_mhz'],
        'platform_clock_hz': platform_info['clock_mhz'] * 1_000_000,
        'mapping_strategy': package.mapping_strategy,
        'has_voltage_types': has_voltage,
        'has_time_types': has_time,
        'signals': signals,
        'register_mappings': register_mappings,
        'cr_numbers_used': cr_numbers_used,
        'total_registers': total_registers,
        'total_bits_used': total_bits_used,
        'total_bits_available': total_bits_available,
        'efficiency_percent': efficiency_percent,
    }

    return context


def generate_vhdl(
    yaml_path: Path,
    output_dir: Path,
    template_dir: Path
) -> None:
    """Generate VHDL shim and main files from YAML specification."""

    print("=" * 80)
    print("BasicAppDataTypes VHDL Generator v2.0")
    print("=" * 80)

    # Load YAML spec
    print(f"\n[1/5] Loading YAML specification: {yaml_path}")
    spec = load_yaml_spec(yaml_path)
    print(f"       App: {spec['app_name']}")
    print(f"       Platform: {spec['platform']}")
    print(f"       Datatypes: {len(spec['datatypes'])}")

    # Get platform info
    if spec['platform'] not in PLATFORM_MAP:
        raise ValueError(f"Unknown platform: {spec['platform']}")
    platform_info = PLATFORM_MAP[spec['platform']]

    # Create register package
    print(f"\n[2/5] Creating register package...")
    package = create_register_package(spec)
    print(f"       Package: {package.app_name}")
    print(f"       Strategy: {package.mapping_strategy}")

    # Prepare template context
    print(f"\n[3/5] Preparing template context...")
    context = prepare_template_context(package, yaml_path, platform_info)
    print(f"       Signals: {len(context['signals'])}")
    print(f"       Registers used: {context['total_registers']} (CR{min(context['cr_numbers_used'])}-CR{max(context['cr_numbers_used'])})")
    print(f"       Efficiency: {context['efficiency_percent']}% ({context['total_bits_used']}/{context['total_bits_available']} bits)")

    # Setup Jinja2 environment
    jinja_env = Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Generate shim
    print(f"\n[4/5] Generating shim file...")
    shim_template = jinja_env.get_template('shim.vhd.j2')
    shim_output = shim_template.render(context)
    shim_path = output_dir / f"{package.app_name}_custom_inst_shim.vhd"
    output_dir.mkdir(parents=True, exist_ok=True)
    shim_path.write_text(shim_output)
    print(f"       Written: {shim_path}")
    print(f"       Size: {len(shim_output)} bytes")

    # Generate main
    print(f"\n[5/5] Generating main template file...")
    main_template = jinja_env.get_template('main.vhd.j2')
    main_output = main_template.render(context)
    main_path = output_dir / f"{package.app_name}_custom_inst_main.vhd"

    # Only write main if it doesn't exist (don't overwrite hand-written logic)
    if main_path.exists():
        print(f"       Skipped: {main_path} (already exists)")
    else:
        main_path.write_text(main_output)
        print(f"       Written: {main_path}")
        print(f"       Size: {len(main_output)} bytes")

    print("\n" + "=" * 80)
    print("✅ Generation Complete")
    print("=" * 80)
    print(f"\nGenerated files in: {output_dir}/")
    print(f"  - {package.app_name}_custom_inst_shim.vhd (auto-generated, always overwritten)")
    if not main_path.exists():
        print(f"  - {package.app_name}_custom_inst_main.vhd (template, customize for your app)")

    print(f"\nRegister Mapping Summary ({context['mapping_strategy']} strategy):")
    for mapping in context['register_mappings']:
        fields_str = " | ".join(
            f"{f['name']}[{f['bits']}]" for f in mapping['fields']
        )
        print(f"  CR{mapping['register_index']}: {fields_str}")

    print(f"\nNext steps:")
    print(f"1. Implement application logic in {package.app_name}_custom_inst_main.vhd")
    print(f"2. Add any custom signals/state machines needed")
    print(f"3. Test with CocotB or hardware deployment")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate VHDL code from BasicAppDataTypes YAML specification'
    )
    parser.add_argument(
        'yaml_file',
        type=Path,
        help='Path to YAML specification file'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=None,
        help='Output directory (default: generated/<app_name>/)'
    )
    parser.add_argument(
        '--template-dir',
        type=Path,
        default=project_root / 'shared' / 'custom_inst' / 'templates',
        help='Template directory (default: shared/custom_inst/templates/)'
    )

    args = parser.parse_args()

    # Validate input
    if not args.yaml_file.exists():
        print(f"Error: YAML file not found: {args.yaml_file}", file=sys.stderr)
        sys.exit(1)

    # Determine output directory
    if args.output_dir is None:
        # Extract app name from YAML to use in default output path
        with open(args.yaml_file, 'r') as f:
            spec = yaml.safe_load(f)
        app_name = spec.get('app_name', 'unknown_app')
        args.output_dir = project_root / 'generated' / app_name

    # Generate VHDL
    try:
        generate_vhdl(args.yaml_file, args.output_dir, args.template_dir)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
