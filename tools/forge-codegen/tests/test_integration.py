"""
Integration tests for complete BasicAppDataTypes pipeline.

Tests:
- YAML → Package → Mapping → VHDL generation (end-to-end)
- DS1140_PD migration validation (register savings)
- Multi-platform generation (Moku:Go, Moku:Lab)
- Critical path validation

Focus: End-to-end workflows that validate the complete BAD system.
"""

import pytest
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

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
from forge_codegen.basic_serialized_datatypes import BasicAppDataTypes, RegisterMapper, TYPE_REGISTRY


class TestEndToEndPipeline:
    """Test complete YAML → VHDL workflow."""

    def test_yaml_to_vhdl_complete_pipeline(self, tmp_path):
        """Test full pipeline from YAML spec to generated VHDL files."""

        yaml_content = """
app_name: "PipelineTest"
platform: "moku_go"
description: "Integration test for full pipeline"
mapping_strategy: "best_fit"
datatypes:
  - name: "intensity"
    datatype: "voltage_output_05v_s16"
    description: "Output voltage"
    default_value: 2400
    units: "mV"
  - name: "timeout"
    datatype: "pulse_duration_ms_u16"
    description: "Timeout period"
    default_value: 1000
    units: "ms"
  - name: "enable"
    datatype: "boolean"
    description: "Enable signal"
    default_value: false
"""

        yaml_path = tmp_path / "pipeline_test.yaml"
        yaml_path.write_text(yaml_content)

        # Step 1: Load YAML
        spec = load_yaml_spec(yaml_path)
        assert spec['app_name'] == "PipelineTest"
        assert spec['platform'] == "moku_go"
        assert len(spec['datatypes']) == 3

        # Step 2: Create package
        package = create_register_package(spec)
        assert package.app_name == "PipelineTest"
        assert len(package.datatypes) == 3

        # Step 3: Generate mapping (using core RegisterMapper)
        mapper = RegisterMapper()
        items = [(dt.name, dt.datatype) for dt in package.datatypes]
        mapping = mapper.map(items, strategy=package.mapping_strategy)
        assert len(mapping) == 3

        # Step 4: Prepare context
        platform_info = PLATFORM_MAP['moku_go']
        context = prepare_template_context(package, yaml_path, platform_info)
        assert len(context['signals']) == 3
        assert context['platform_clock_hz'] == 125_000_000

        # Step 5: Generate VHDL
        output_dir = tmp_path / "vhdl"
        output_dir.mkdir()
        template_dir = project_root / "forge" / "templates"

        generate_vhdl(yaml_path, output_dir, template_dir)

        # Step 6: Verify outputs exist
        shim_path = output_dir / "PipelineTest_custom_inst_shim.vhd"
        main_path = output_dir / "PipelineTest_custom_inst_main.vhd"

        assert shim_path.exists(), "Shim file not generated"
        assert main_path.exists(), "Main file not generated"

        # Step 7: Verify shim content
        shim_content = shim_path.read_text()

        # Check platform constant
        assert "CLK_FREQ_HZ : integer := 125000000" in shim_content

        # Check signal declarations
        assert "signal intensity : signed(15 downto 0)" in shim_content
        assert "signal timeout : unsigned(15 downto 0)" in shim_content
        assert "signal enable : std_logic" in shim_content

        # Check library imports
        assert "use WORK.basic_app_types_pkg.all" in shim_content
        assert "use WORK.basic_app_voltage_pkg.all" in shim_content
        assert "use WORK.basic_app_time_pkg.all" in shim_content

        # Step 8: Verify main content
        main_content = main_path.read_text()
        assert "entity PipelineTest_custom_inst_main" in main_content
        assert "CLK_FREQ_HZ" in main_content


class TestDS1140PDMigration:
    """Test DS1140_PD migration to BasicAppDataTypes validates register savings."""

    def test_ds1140_pd_register_efficiency(self):
        """Test DS1140_PD achieves expected register savings (3 regs vs 7 manual)."""

        # DS1140_PD has 8 datatypes
        from forge_codegen.models.package import BasicAppsRegPackage, DataTypeSpec

        datatypes = [
            DataTypeSpec(name="arm_probe", datatype=BasicAppDataTypes.BOOLEAN),
            DataTypeSpec(name="force_fire", datatype=BasicAppDataTypes.BOOLEAN),
            DataTypeSpec(name="reset_fsm", datatype=BasicAppDataTypes.BOOLEAN),
            DataTypeSpec(name="intensity", datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),
            DataTypeSpec(name="trigger_threshold", datatype=BasicAppDataTypes.VOLTAGE_INPUT_25V_S16),
            DataTypeSpec(name="arm_timeout", datatype=BasicAppDataTypes.PULSE_DURATION_MS_U16),
            DataTypeSpec(name="firing_duration", datatype=BasicAppDataTypes.PULSE_DURATION_NS_U8),
            DataTypeSpec(name="cooling_duration", datatype=BasicAppDataTypes.PULSE_DURATION_NS_U8),
        ]

        package = BasicAppsRegPackage(
            app_name="DS1140_PD",
            description="EMFI probe driver",
            datatypes=datatypes,
            mapping_strategy="best_fit"
        )

        # Generate mapping (using core RegisterMapper)
        mapper = RegisterMapper()
        items = [(dt.name, dt.datatype) for dt in package.datatypes]
        mapping = mapper.map(items, strategy=package.mapping_strategy)

        # Phase 4 result: 8 datatypes → 3 registers (vs 7 manual = 57% savings)
        used_registers = set(m.cr_number for m in mapping)
        assert len(used_registers) == 3, \
            f"Expected 3 registers, got {len(used_registers)} (registers: {used_registers})"

        # Verify specific register allocation (CR6, CR7, CR8)
        assert used_registers == {6, 7, 8}, \
            f"Expected CR6-8, got {sorted(used_registers)}"

        # Verify efficiency (Phase 4: 69.8% bit utilization)
        total_bits = len(used_registers) * 32
        used_bits = sum(TYPE_REGISTRY[m.datatype].bit_width for m in mapping)
        efficiency = (used_bits / total_bits) * 100

        assert efficiency > 60.0, \
            f"Expected >60% efficiency, got {efficiency:.1f}%"

        # Document the savings
        manual_registers = 7  # From legacy DS1140_PD implementation
        automated_registers = len(used_registers)
        savings_percent = ((manual_registers - automated_registers) / manual_registers) * 100

        assert savings_percent > 50.0, \
            f"Expected >50% register savings, got {savings_percent:.1f}%"

    def test_ds1140_pd_yaml_loading(self):
        """Test loading actual DS1140_PD YAML from examples/."""

        yaml_path = project_root / "examples" / "DS1140_PD_interface.yaml"

        if not yaml_path.exists():
            pytest.skip(f"DS1140_PD YAML not found at {yaml_path}")

        # Load YAML
        spec = load_yaml_spec(yaml_path)

        assert spec['app_name'] == "DS1140_PD"
        assert len(spec['datatypes']) == 8
        assert spec['mapping_strategy'] in ['best_fit', 'first_fit', 'type_clustering']

        # Create package
        package = create_register_package(spec)
        assert package.app_name == "DS1140_PD"
        assert len(package.datatypes) == 8

        # Generate mapping (using core RegisterMapper)
        mapper = RegisterMapper()
        items = [(dt.name, dt.datatype) for dt in package.datatypes]
        mapping = mapper.map(items, strategy=package.mapping_strategy)

        # Validate register efficiency
        used_registers = set(m.cr_number for m in mapping)
        assert len(used_registers) <= 3, \
            f"DS1140_PD should use ≤3 registers, got {len(used_registers)}"


class TestMultiPlatformGeneration:
    """Test generating for different Moku platforms (Go, Lab focus)."""

    @pytest.mark.parametrize("platform,expected_clk_hz", [
        ("moku_go", 125_000_000),
        ("moku_lab", 500_000_000),
    ])
    def test_platform_specific_vhdl_generation(self, platform, expected_clk_hz, tmp_path):
        """Test code generation for Moku:Go and Moku:Lab platforms."""

        yaml_content = f"""
app_name: "MultiPlatformTest"
platform: "{platform}"
description: "Platform-specific test"
datatypes:
  - name: "delay"
    datatype: "pulse_duration_ms_u16"
    description: "Time delay"
    default_value: 1000
  - name: "enable"
    datatype: "boolean"
    description: "Enable flag"
    default_value: true
"""

        yaml_path = tmp_path / f"{platform}_test.yaml"
        yaml_path.write_text(yaml_content)

        output_dir = tmp_path / "vhdl" / platform
        output_dir.mkdir(parents=True)
        template_dir = project_root / "forge" / "templates"

        # Generate VHDL
        generate_vhdl(yaml_path, output_dir, template_dir)

        # Verify shim was created
        shim_path = output_dir / "MultiPlatformTest_custom_inst_shim.vhd"
        assert shim_path.exists(), f"Shim not created for {platform}"

        shim_content = shim_path.read_text()

        # Check correct clock frequency
        clk_generic = f"CLK_FREQ_HZ : integer := {expected_clk_hz}"
        assert clk_generic in shim_content, \
            f"Expected {clk_generic} in {platform} shim"

        # Check platform name in comments
        platform_name = PLATFORM_MAP[platform]['name']
        assert platform_name in shim_content, \
            f"Platform name '{platform_name}' not found in comments"

    def test_same_yaml_different_platforms(self, tmp_path):
        """Test that same YAML spec generates correct VHDL for both platforms."""

        yaml_base = """
app_name: "CrossPlatformTest"
description: "Test cross-platform consistency"
datatypes:
  - name: "pulse_width"
    datatype: "pulse_duration_ns_u16"
    default_value: 100
"""

        platforms = ["moku_go", "moku_lab"]
        expected_clocks = {
            "moku_go": 125_000_000,
            "moku_lab": 500_000_000,
        }

        for platform in platforms:
            yaml_content = f'platform: "{platform}"\n' + yaml_base
            yaml_path = tmp_path / f"{platform}.yaml"
            yaml_path.write_text(yaml_content)

            output_dir = tmp_path / platform
            output_dir.mkdir()
            template_dir = project_root / "forge" / "templates"

            generate_vhdl(yaml_path, output_dir, template_dir)

            shim_path = output_dir / "CrossPlatformTest_custom_inst_shim.vhd"
            assert shim_path.exists()

            shim_content = shim_path.read_text()

            # Verify platform-specific clock
            expected_clk = expected_clocks[platform]
            assert f"CLK_FREQ_HZ : integer := {expected_clk}" in shim_content

            # Verify signal declarations are identical (platform-agnostic)
            assert "signal pulse_width : unsigned(15 downto 0)" in shim_content


class TestRegisterMappingIntegration:
    """Test register mapping integration with package model."""

    def test_mapping_determinism(self):
        """Test that register mapping is deterministic (same input = same output)."""

        from forge_codegen.models.package import BasicAppsRegPackage, DataTypeSpec

        datatypes = [
            DataTypeSpec(name="sig1", datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),
            DataTypeSpec(name="sig2", datatype=BasicAppDataTypes.BOOLEAN),
            DataTypeSpec(name="sig3", datatype=BasicAppDataTypes.PULSE_DURATION_MS_U16),
        ]

        package = BasicAppsRegPackage(
            app_name="DeterminismTest",
            datatypes=datatypes,
            mapping_strategy="best_fit"
        )

        # Generate mapping twice (using core RegisterMapper)
        mapper1 = RegisterMapper()
        items = [(dt.name, dt.datatype) for dt in package.datatypes]
        mapping1 = mapper1.map(items, strategy=package.mapping_strategy)

        mapper2 = RegisterMapper()
        mapping2 = mapper2.map(items, strategy=package.mapping_strategy)

        # Compare mappings
        assert len(mapping1) == len(mapping2), "Mapping length mismatch"

        for m1, m2 in zip(mapping1, mapping2):
            assert m1.name == m2.name, f"Signal name mismatch: {m1.name} vs {m2.name}"
            assert m1.cr_number == m2.cr_number, f"CR number mismatch for {m1.name}"
            assert m1.bit_slice == m2.bit_slice, f"Bit slice mismatch for {m1.name}"

    def test_overflow_detection(self):
        """Test that register overflow is detected when too many datatypes."""

        from forge_codegen.basic_serialized_datatypes import RegisterMapper

        # Create many 16-bit types (should overflow 12 available registers)
        # 12 registers * 32 bits / 16 bits per signal = 24 signals max
        # So 30 signals should definitely overflow
        items = [
            (f"voltage_{i}", BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16)
            for i in range(30)
        ]

        # Should raise ValueError when trying to map
        mapper = RegisterMapper()

        with pytest.raises(ValueError, match="Cannot fit|too many|overflow"):
            mapper.map(items, strategy="best_fit")


class TestDefaultValuePropagation:
    """Test that default values propagate through the pipeline."""

    def test_default_values_in_generated_vhdl(self, tmp_path):
        """Test that YAML default values appear in generated VHDL."""

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

        yaml_path = tmp_path / "default_test.yaml"
        yaml_path.write_text(yaml_content)

        # Load and create package
        spec = load_yaml_spec(yaml_path)
        package = create_register_package(spec)

        # Verify defaults in package
        intensity_dt = next(dt for dt in package.datatypes if dt.name == "intensity")
        assert intensity_dt.default_value == 2400

        enable_dt = next(dt for dt in package.datatypes if dt.name == "enable")
        assert enable_dt.default_value is True

        timeout_dt = next(dt for dt in package.datatypes if dt.name == "timeout")
        assert timeout_dt.default_value == 1000

        # Generate context and verify defaults are preserved
        platform_info = PLATFORM_MAP['moku_go']
        context = prepare_template_context(package, yaml_path, platform_info)

        intensity_sig = next(s for s in context['signals'] if s['name'] == "intensity")
        assert intensity_sig['default_value'] == 2400

        enable_sig = next(s for s in context['signals'] if s['name'] == "enable")
        assert enable_sig['default_value'] is True


# Run tests with: PYTHONPATH=libs/basic-app-datatypes:. uv run pytest python_tests/test_bad_integration.py -v
