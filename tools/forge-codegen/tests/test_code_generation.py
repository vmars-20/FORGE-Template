"""
Tests for tools/generate_custom_inst_v2.py code generator.

Validates:
- YAML parsing and validation
- Template rendering (shim + main)
- Platform constant injection (Moku:Go, Moku:Lab)
- Type conversion function selection
- Register mapping integration

Focus: Critical paths for BasicAppDataTypes code generation.
"""

import pytest
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from forge_codegen.generator.codegen import (
    load_yaml_spec,
    create_register_package,
    prepare_template_context,
    generate_vhdl,
    PLATFORM_MAP,
)
from forge_codegen.basic_serialized_datatypes import BasicAppDataTypes


class TestYAMLParsing:
    """Test YAML specification parsing and validation."""

    def test_load_valid_yaml(self, tmp_path):
        """Test loading valid YAML specification."""
        yaml_content = """
package_version: "2.0"
app_name: "TestApp"
platform: "moku_go"
datatypes:
  - name: "enable"
    datatype: "boolean"
    description: "Enable flag"
    default_value: false
"""
        yaml_path = tmp_path / "test.yaml"
        yaml_path.write_text(yaml_content)

        spec = load_yaml_spec(yaml_path)

        assert spec['app_name'] == 'TestApp'
        assert spec['platform'] == 'moku_go'
        assert len(spec['datatypes']) == 1
        assert spec['datatypes'][0]['name'] == 'enable'

    def test_load_yaml_missing_app_name(self, tmp_path):
        """Test that YAML without app_name is rejected."""
        yaml_content = """
datatypes:
  - name: "enable"
    datatype: "boolean"
"""
        yaml_path = tmp_path / "test.yaml"
        yaml_path.write_text(yaml_content)

        with pytest.raises(ValueError, match="Missing required field.*app_name"):
            load_yaml_spec(yaml_path)

    def test_load_yaml_default_platform(self, tmp_path, capsys):
        """Test that YAML defaults to moku_go when platform omitted."""
        yaml_content = """
app_name: "TestApp"
datatypes:
  - name: "enable"
    datatype: "boolean"
"""
        yaml_path = tmp_path / "test.yaml"
        yaml_path.write_text(yaml_content)

        spec = load_yaml_spec(yaml_path)

        assert spec['platform'] == 'moku_go'
        captured = capsys.readouterr()
        assert "defaulting to moku_go" in captured.out

    def test_load_yaml_default_strategy(self, tmp_path, capsys):
        """Test that YAML defaults to best_fit strategy."""
        yaml_content = """
app_name: "TestApp"
platform: "moku_go"
datatypes:
  - name: "enable"
    datatype: "boolean"
"""
        yaml_path = tmp_path / "test.yaml"
        yaml_path.write_text(yaml_content)

        spec = load_yaml_spec(yaml_path)

        assert spec['mapping_strategy'] == 'best_fit'
        captured = capsys.readouterr()
        assert "defaulting to best_fit" in captured.out


class TestPackageCreation:
    """Test BasicAppsRegPackage creation from YAML."""

    def test_create_package_from_spec(self, tmp_path):
        """Test creating package from valid YAML spec."""
        yaml_content = """
app_name: "TestApp"
platform: "moku_go"
description: "Test application"
mapping_strategy: "first_fit"
datatypes:
  - name: "intensity"
    datatype: "voltage_output_05v_s16"
    description: "Probe intensity"
    default_value: 2400
    units: "mV"
  - name: "enable"
    datatype: "boolean"
    description: "Enable flag"
    default_value: false
"""
        yaml_path = tmp_path / "test.yaml"
        yaml_path.write_text(yaml_content)

        spec = load_yaml_spec(yaml_path)
        package = create_register_package(spec)

        assert package.app_name == "TestApp"
        # Note: platform is stored in spec, not package (package is platform-agnostic)
        assert package.description == "Test application"
        assert package.mapping_strategy == "first_fit"
        assert len(package.datatypes) == 2

        # Verify datatype specs
        intensity_spec = package.datatypes[0]
        assert intensity_spec.name == "intensity"
        assert intensity_spec.datatype == BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16
        assert intensity_spec.default_value == 2400
        assert intensity_spec.units == "mV"

        enable_spec = package.datatypes[1]
        assert enable_spec.name == "enable"
        assert enable_spec.datatype == BasicAppDataTypes.BOOLEAN
        assert enable_spec.default_value is False

    def test_create_package_invalid_datatype(self, tmp_path):
        """Test that invalid datatype names are rejected."""
        yaml_content = """
app_name: "TestApp"
platform: "moku_go"
datatypes:
  - name: "bad_type"
    datatype: "nonexistent_type"
"""
        yaml_path = tmp_path / "test.yaml"
        yaml_path.write_text(yaml_content)

        spec = load_yaml_spec(yaml_path)

        with pytest.raises(ValueError, match="Unknown datatype"):
            create_register_package(spec)


class TestPlatformConstants:
    """Test platform-specific constant injection."""

    @pytest.mark.parametrize("platform,expected_clk_mhz", [
        ("moku_go", 125),
        ("moku_lab", 500),
    ])
    def test_platform_clock_frequency(self, platform, expected_clk_mhz, tmp_path):
        """Test that correct clock frequency is used for each platform."""
        yaml_content = f"""
app_name: "PlatformTest"
platform: "{platform}"
datatypes:
  - name: "delay"
    datatype: "pulse_duration_ms_u16"
    default_value: 1000
"""
        yaml_path = tmp_path / "test.yaml"
        yaml_path.write_text(yaml_content)

        spec = load_yaml_spec(yaml_path)
        package = create_register_package(spec)
        platform_info = PLATFORM_MAP[platform]
        context = prepare_template_context(package, yaml_path, platform_info)

        assert context['platform_clock_hz'] == expected_clk_mhz * 1_000_000
        assert context['platform_name'] == platform_info['name']
        assert context['platform_clock_mhz'] == expected_clk_mhz

    def test_platform_map_completeness(self):
        """Test that PLATFORM_MAP has all required platforms."""
        required_platforms = ['moku_go', 'moku_lab']  # Phase 5 focus

        for platform in required_platforms:
            assert platform in PLATFORM_MAP, f"Missing platform: {platform}"
            platform_info = PLATFORM_MAP[platform]
            assert 'name' in platform_info
            assert 'clock_mhz' in platform_info
            assert 'slots' in platform_info


class TestTypeConversionFunctions:
    """Test that correct type conversion functions are selected."""

    def test_voltage_type_function_selection(self, tmp_path):
        """Test voltage type selects correct conversion function."""
        yaml_content = """
app_name: "VoltageTest"
platform: "moku_go"
datatypes:
  - name: "output_voltage"
    datatype: "voltage_output_05v_s16"
    default_value: 2500
  - name: "input_voltage"
    datatype: "voltage_input_25v_s16"
    default_value: 12000
"""
        yaml_path = tmp_path / "test.yaml"
        yaml_path.write_text(yaml_content)

        spec = load_yaml_spec(yaml_path)
        package = create_register_package(spec)
        platform_info = PLATFORM_MAP['moku_go']
        context = prepare_template_context(package, yaml_path, platform_info)

        # Check that voltage package is required
        assert context['has_voltage_types'] is True

        # Check signal metadata includes correct type info
        output_sig = next(s for s in context['signals'] if s['name'] == 'output_voltage')
        assert 'signed' in output_sig['vhdl_type']

        input_sig = next(s for s in context['signals'] if s['name'] == 'input_voltage')
        assert 'signed' in input_sig['vhdl_type']

    def test_time_type_function_selection(self, tmp_path):
        """Test time type is correctly identified."""
        yaml_content = """
app_name: "TimeTest"
platform: "moku_go"
datatypes:
  - name: "pulse_width_ns"
    datatype: "pulse_duration_ns_u16"
    default_value: 100
  - name: "delay_ms"
    datatype: "pulse_duration_ms_u16"
    default_value: 1000
"""
        yaml_path = tmp_path / "test.yaml"
        yaml_path.write_text(yaml_content)

        spec = load_yaml_spec(yaml_path)
        package = create_register_package(spec)
        platform_info = PLATFORM_MAP['moku_go']
        context = prepare_template_context(package, yaml_path, platform_info)

        # Check that time package is required
        assert context['has_time_types'] is True

        # Check signal metadata
        pulse_sig = next(s for s in context['signals'] if s['name'] == 'pulse_width_ns')
        assert 'unsigned' in pulse_sig['vhdl_type']

        delay_sig = next(s for s in context['signals'] if s['name'] == 'delay_ms')
        assert 'unsigned' in delay_sig['vhdl_type']

    def test_boolean_type_single_bit(self, tmp_path):
        """Test boolean type is single bit (std_logic)."""
        yaml_content = """
app_name: "BooleanTest"
platform: "moku_go"
datatypes:
  - name: "enable"
    datatype: "boolean"
    default_value: false
  - name: "arm_probe"
    datatype: "boolean"
    default_value: true
"""
        yaml_path = tmp_path / "test.yaml"
        yaml_path.write_text(yaml_content)

        spec = load_yaml_spec(yaml_path)
        package = create_register_package(spec)
        platform_info = PLATFORM_MAP['moku_go']
        context = prepare_template_context(package, yaml_path, platform_info)

        # Check signal metadata for booleans
        enable_sig = next(s for s in context['signals'] if s['name'] == 'enable')
        assert enable_sig['vhdl_type'] == 'std_logic'
        assert enable_sig['is_boolean'] is True

        arm_sig = next(s for s in context['signals'] if s['name'] == 'arm_probe')
        assert arm_sig['vhdl_type'] == 'std_logic'
        assert arm_sig['is_boolean'] is True


class TestRegisterMapping:
    """Test register mapping integration."""

    def test_mapping_accuracy_ds1140_pd(self, tmp_path):
        """Test DS1140_PD achieves expected register packing (3 regs from 8 types)."""
        # DS1140_PD spec (from Phase 4)
        yaml_content = """
app_name: "DS1140_PD"
platform: "moku_go"
mapping_strategy: "best_fit"
datatypes:
  - name: "arm_probe"
    datatype: "boolean"
  - name: "force_fire"
    datatype: "boolean"
  - name: "reset_fsm"
    datatype: "boolean"
  - name: "intensity"
    datatype: "voltage_output_05v_s16"
  - name: "trigger_threshold"
    datatype: "voltage_input_25v_s16"
  - name: "arm_timeout"
    datatype: "pulse_duration_ms_u16"
  - name: "firing_duration"
    datatype: "pulse_duration_ns_u8"
  - name: "cooling_duration"
    datatype: "pulse_duration_ns_u8"
"""
        yaml_path = tmp_path / "ds1140_pd.yaml"
        yaml_path.write_text(yaml_content)

        spec = load_yaml_spec(yaml_path)
        package = create_register_package(spec)
        platform_info = PLATFORM_MAP['moku_go']
        context = prepare_template_context(package, yaml_path, platform_info)

        # DS1140_PD should use 3 registers (CR6, CR7, CR8)
        used_registers = set()
        for signal in context['signals']:
            reg_num = signal['cr_number']
            used_registers.add(reg_num)

        assert len(used_registers) == 3, f"Expected 3 registers, got {len(used_registers)}"
        assert used_registers == {6, 7, 8}, f"Expected CR6-8, got {used_registers}"

        # Check efficiency (from Phase 4: 69.8%)
        assert context['efficiency_percent'] > 60.0, \
            f"Expected >60% efficiency, got {context['efficiency_percent']}%"


class TestVHDLGeneration:
    """Test VHDL file generation."""

    def test_generate_vhdl_files(self, tmp_path):
        """Test generating VHDL shim and main files."""
        yaml_content = """
app_name: "SimpleApp"
platform: "moku_go"
datatypes:
  - name: "enable"
    datatype: "boolean"
    description: "Enable signal"
    default_value: false
  - name: "intensity"
    datatype: "voltage_output_05v_s16"
    description: "Output voltage"
    default_value: 2500
"""
        yaml_path = tmp_path / "simple.yaml"
        yaml_path.write_text(yaml_content)

        output_dir = tmp_path / "generated"
        output_dir.mkdir()

        # Generate VHDL files
        template_dir = project_root / "forge" / "templates"
        generate_vhdl(yaml_path, output_dir, template_dir)

        # Check files were created
        shim_path = output_dir / "SimpleApp_custom_inst_shim.vhd"
        main_path = output_dir / "SimpleApp_custom_inst_main.vhd"

        assert shim_path.exists(), "Shim file not created"
        assert main_path.exists(), "Main file not created"

        # Verify shim content
        shim_content = shim_path.read_text()

        # Check for platform constant
        assert "CLK_FREQ_HZ : integer := 125000000" in shim_content, \
            "Moku:Go clock frequency not found"

        # Check for signal declarations
        assert "signal enable : std_logic" in shim_content, \
            "Boolean signal not declared"
        assert "signal intensity : signed(15 downto 0)" in shim_content, \
            "Voltage signal not declared"

        # Check for proper library imports
        assert "use WORK.basic_app_types_pkg.all" in shim_content
        assert "use WORK.basic_app_voltage_pkg.all" in shim_content

        # Verify main content
        main_content = main_path.read_text()
        assert "entity SimpleApp_custom_inst_main" in main_content
        assert "CLK_FREQ_HZ" in main_content

    def test_generate_vhdl_moku_lab_platform(self, tmp_path):
        """Test generating VHDL for Moku:Lab platform (500 MHz)."""
        yaml_content = """
app_name: "LabApp"
platform: "moku_lab"
datatypes:
  - name: "delay"
    datatype: "pulse_duration_ms_u16"
    default_value: 1000
"""
        yaml_path = tmp_path / "lab.yaml"
        yaml_path.write_text(yaml_content)

        output_dir = tmp_path / "generated"
        output_dir.mkdir()

        template_dir = project_root / "forge" / "templates"
        generate_vhdl(yaml_path, output_dir, template_dir)

        shim_path = output_dir / "LabApp_custom_inst_shim.vhd"
        assert shim_path.exists()

        shim_content = shim_path.read_text()

        # Check for Moku:Lab clock frequency (500 MHz)
        assert "CLK_FREQ_HZ : integer := 500000000" in shim_content, \
            "Moku:Lab clock frequency not found"

        # Check for platform comment
        assert "Moku:Lab" in shim_content


class TestDefaultValues:
    """Test default value initialization in generated VHDL."""

    def test_default_values_in_context(self, tmp_path):
        """Test that default values are included in template context."""
        yaml_content = """
app_name: "DefaultTest"
platform: "moku_go"
datatypes:
  - name: "intensity"
    datatype: "voltage_output_05v_s16"
    default_value: 2400
  - name: "enable"
    datatype: "boolean"
    default_value: true
  - name: "timeout"
    datatype: "pulse_duration_ms_u16"
    default_value: 1000
"""
        yaml_path = tmp_path / "defaults.yaml"
        yaml_path.write_text(yaml_content)

        spec = load_yaml_spec(yaml_path)
        package = create_register_package(spec)
        platform_info = PLATFORM_MAP['moku_go']
        context = prepare_template_context(package, yaml_path, platform_info)

        # Verify default values in signal metadata
        intensity_sig = next(s for s in context['signals'] if s['name'] == 'intensity')
        assert intensity_sig['default_value'] == 2400

        enable_sig = next(s for s in context['signals'] if s['name'] == 'enable')
        assert enable_sig['default_value'] is True

        timeout_sig = next(s for s in context['signals'] if s['name'] == 'timeout')
        assert timeout_sig['default_value'] == 1000


# Run tests with: PYTHONPATH=libs/basic-app-datatypes:. uv run pytest python_tests/test_code_generation.py -v
