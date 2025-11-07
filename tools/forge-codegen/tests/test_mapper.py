"""
Integration tests for BADRegisterMapper (Pydantic wrapper).

Tests the Pydantic integration layer that wraps the core RegisterMapper.
Core algorithm tests are in libs/basic-app-datatypes/tests/test_mapper.py.
"""

import pytest
import yaml
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from forge_codegen.models.mapper import (
    BADRegisterConfig,
    BADRegisterMapper,
)
from forge_codegen.basic_serialized_datatypes import BasicAppDataTypes
from forge_codegen.models import AppRegister, RegisterType


class TestBADRegisterConfig:
    """Test BADRegisterConfig Pydantic model."""

    def test_valid_config(self):
        """Test creating valid register config."""
        config = BADRegisterConfig(
            name="intensity",
            datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
            description="Probe intensity control",
            default_value=0
        )

        assert config.name == "intensity"
        assert config.datatype == BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16
        assert config.default_value == 0

    def test_boolean_default_value(self):
        """Test boolean type accepts bool default_value."""
        config = BADRegisterConfig(
            name="enable",
            datatype=BasicAppDataTypes.BOOLEAN,
            description="Enable flag",
            default_value=True
        )

        assert config.default_value is True

    def test_invalid_name_start_with_number(self):
        """Test that names starting with numbers are rejected."""
        with pytest.raises(ValueError, match="must start with letter"):
            BADRegisterConfig(
                name="123invalid",
                datatype=BasicAppDataTypes.BOOLEAN
            )

    def test_invalid_name_special_chars(self):
        """Test that names with special characters are rejected."""
        with pytest.raises(ValueError, match="alphanumeric and underscore"):
            BADRegisterConfig(
                name="invalid-name",
                datatype=BasicAppDataTypes.BOOLEAN
            )

    def test_vhdl_reserved_word(self):
        """Test that VHDL reserved words are rejected."""
        with pytest.raises(ValueError, match="reserved word"):
            BADRegisterConfig(
                name="signal",  # VHDL reserved
                datatype=BasicAppDataTypes.BOOLEAN
            )

    def test_default_value_out_of_range(self):
        """Test that default_value is validated against type constraints."""
        with pytest.raises(ValueError, match="above max"):
            BADRegisterConfig(
                name="bad_voltage",
                datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
                default_value=10000  # Exceeds 5000 mV max
            )

    def test_default_value_below_range(self):
        """Test negative values validated for signed types."""
        with pytest.raises(ValueError, match="below min"):
            BADRegisterConfig(
                name="bad_voltage",
                datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
                default_value=-10000  # Below -5000 mV min
            )

    def test_boolean_wrong_type(self):
        """Test boolean type rejects non-bool default_value."""
        with pytest.raises(ValueError, match="requires bool"):
            BADRegisterConfig(
                name="enable",
                datatype=BasicAppDataTypes.BOOLEAN,
                default_value=1  # Should be True/False
            )


class TestBADRegisterMapper:
    """Test BADRegisterMapper Pydantic wrapper."""

    def test_simple_mapping(self):
        """Test basic register mapping."""
        mapper = BADRegisterMapper(
            registers=[
                BADRegisterConfig(
                    name="intensity",
                    datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16
                ),
                BADRegisterConfig(
                    name="threshold",
                    datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16
                ),
            ],
            strategy="best_fit"
        )

        mappings = mapper.to_register_mappings()

        assert len(mappings) == 2
        # Both should fit in CR6
        assert all(m.cr_number == 6 for m in mappings)

    def test_duplicate_names_rejected(self):
        """Test that duplicate names are rejected."""
        with pytest.raises(ValueError, match="Duplicate register names"):
            BADRegisterMapper(
                registers=[
                    BADRegisterConfig(
                        name="duplicate",
                        datatype=BasicAppDataTypes.BOOLEAN
                    ),
                    BADRegisterConfig(
                        name="duplicate",
                        datatype=BasicAppDataTypes.BOOLEAN
                    ),
                ]
            )

    def test_generate_report(self):
        """Test report generation."""
        mapper = BADRegisterMapper(
            registers=[
                BADRegisterConfig(
                    name="test",
                    datatype=BasicAppDataTypes.BOOLEAN
                ),
            ]
        )

        report = mapper.generate_report()

        assert report.total_bits_used == 1
        assert report.total_bits_available == 384
        assert len(report.register_map) == 1

    def test_save_report_all_formats(self):
        """Test saving reports in all formats."""
        mapper = BADRegisterMapper(
            registers=[
                BADRegisterConfig(name="a", datatype=BasicAppDataTypes.BOOLEAN),
                BADRegisterConfig(name="b", datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),
            ]
        )

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            mapper.save_report(output_dir)

            # Verify all files created
            assert (output_dir / 'mapping_report.txt').exists()
            assert (output_dir / 'mapping_report.md').exists()
            assert (output_dir / 'mapping_comments.vhd').exists()
            assert (output_dir / 'mapping.json').exists()

            # Verify JSON content
            with open(output_dir / 'mapping.json') as f:
                data = json.load(f)
            assert 'mappings' in data
            assert 'summary' in data
            assert len(data['mappings']) == 2

    def test_to_app_registers_backward_compatibility(self):
        """Test conversion to legacy AppRegister format."""
        mapper = BADRegisterMapper(
            registers=[
                BADRegisterConfig(
                    name="enable",
                    datatype=BasicAppDataTypes.BOOLEAN,
                    description="Enable flag"
                ),
                BADRegisterConfig(
                    name="counter",
                    datatype=BasicAppDataTypes.PULSE_DURATION_NS_U8,
                    description="8-bit counter"
                ),
            ]
        )

        app_registers = mapper.to_app_registers()

        assert len(app_registers) == 2
        assert all(isinstance(r, AppRegister) for r in app_registers)

        # Check types mapped correctly (best_fit sorts by size, so counter comes first)
        reg_by_name = {r.name: r for r in app_registers}
        assert reg_by_name['enable'].reg_type == RegisterType.BUTTON
        assert reg_by_name['counter'].reg_type == RegisterType.COUNTER_8BIT


class TestDS1140PDIntegration:
    """Test DS1140_PD register mapping (integration test)."""

    def test_ds1140_pd_mapping_from_pydantic(self):
        """Test DS1140_PD mapping using Pydantic models."""
        # Define DS1140_PD registers using Pydantic
        mapper = BADRegisterMapper(
            registers=[
                BADRegisterConfig(
                    name="arm_probe",
                    datatype=BasicAppDataTypes.BOOLEAN,
                    description="Arm the EMFI probe",
                    default_value=False
                ),
                BADRegisterConfig(
                    name="force_fire",
                    datatype=BasicAppDataTypes.BOOLEAN,
                    description="Force immediate fire",
                    default_value=False
                ),
                BADRegisterConfig(
                    name="reset_fsm",
                    datatype=BasicAppDataTypes.BOOLEAN,
                    description="Reset FSM to idle",
                    default_value=False
                ),
                BADRegisterConfig(
                    name="clock_divider",
                    datatype=BasicAppDataTypes.PULSE_DURATION_NS_U8,
                    description="Clock divider for timing",
                    default_value=1
                ),
                BADRegisterConfig(
                    name="arm_timeout",
                    datatype=BasicAppDataTypes.PULSE_DURATION_MS_U16,
                    description="Arming timeout",
                    default_value=1000
                ),
                BADRegisterConfig(
                    name="firing_duration",
                    datatype=BasicAppDataTypes.PULSE_DURATION_NS_U8,
                    description="Pulse firing duration",
                    default_value=50
                ),
                BADRegisterConfig(
                    name="cooling_duration",
                    datatype=BasicAppDataTypes.PULSE_DURATION_NS_U8,
                    description="Cooling period duration",
                    default_value=100
                ),
                BADRegisterConfig(
                    name="trigger_threshold",
                    datatype=BasicAppDataTypes.VOLTAGE_INPUT_25V_S16,
                    description="Trigger threshold voltage",
                    default_value=0
                ),
                BADRegisterConfig(
                    name="intensity",
                    datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
                    description="Probe intensity",
                    default_value=0
                ),
            ],
            strategy="best_fit"
        )

        mappings = mapper.to_register_mappings()
        report = mapper.generate_report()

        # Verify register savings
        registers_used = len(report.register_map)
        manual_registers = 9  # Current system: one per type

        print(f"\nDS1140_PD Mapping Results:")
        print(f"  Manual system: {manual_registers} registers")
        print(f"  BAD system: {registers_used} registers")
        print(f"  Savings: {manual_registers - registers_used} registers ({((manual_registers - registers_used) / manual_registers) * 100:.1f}%)")
        print(f"\n{report.to_ascii_art()}")

        # Assertions
        assert registers_used <= 4, f"Expected ≤4 registers, got {registers_used}"

        savings_percent = ((manual_registers - registers_used) / manual_registers) * 100
        assert savings_percent >= 50, f"Expected ≥50% savings, got {savings_percent:.1f}%"

        # Verify total bits
        assert report.total_bits_used == 75  # 3x1 + 3x8 + 3x16 = 75 bits

    def test_ds1140_pd_strategies_comparison(self):
        """Compare different packing strategies for DS1140_PD."""
        registers = [
            BADRegisterConfig(name="arm_probe", datatype=BasicAppDataTypes.BOOLEAN),
            BADRegisterConfig(name="force_fire", datatype=BasicAppDataTypes.BOOLEAN),
            BADRegisterConfig(name="reset_fsm", datatype=BasicAppDataTypes.BOOLEAN),
            BADRegisterConfig(name="clock_divider", datatype=BasicAppDataTypes.PULSE_DURATION_NS_U8),
            BADRegisterConfig(name="arm_timeout", datatype=BasicAppDataTypes.PULSE_DURATION_MS_U16),
            BADRegisterConfig(name="firing_duration", datatype=BasicAppDataTypes.PULSE_DURATION_NS_U8),
            BADRegisterConfig(name="cooling_duration", datatype=BasicAppDataTypes.PULSE_DURATION_NS_U8),
            BADRegisterConfig(name="trigger_threshold", datatype=BasicAppDataTypes.VOLTAGE_INPUT_25V_S16),
            BADRegisterConfig(name="intensity", datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),
        ]

        results = {}
        for strategy in ["first_fit", "best_fit", "type_clustering"]:
            mapper = BADRegisterMapper(registers=registers, strategy=strategy)
            report = mapper.generate_report()
            results[strategy] = len(report.register_map)

        print(f"\nStrategy Comparison:")
        for strategy, num_regs in results.items():
            print(f"  {strategy}: {num_regs} registers")

        # All strategies should achieve good savings
        assert all(num <= 5 for num in results.values()), "All strategies should use ≤5 registers"


class TestYAMLIntegration:
    """Test YAML file integration."""

    def test_from_yaml(self):
        """Test loading BADRegisterMapper from YAML."""
        yaml_content = """
bad_registers:
  strategy: best_fit
  registers:
    - name: intensity
      datatype: voltage_output_05v_s16
      description: "Probe intensity"
      default_value: 0

    - name: enable
      datatype: boolean
      description: "Enable flag"
      default_value: false
"""

        with TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / 'test_config.yaml'
            with open(yaml_path, 'w') as f:
                f.write(yaml_content)

            mapper = BADRegisterMapper.from_yaml(yaml_path)

            assert len(mapper.registers) == 2
            assert mapper.strategy == "best_fit"
            assert mapper.registers[0].name == "intensity"
            assert mapper.registers[1].name == "enable"

    def test_yaml_missing_section(self):
        """Test error when YAML missing bad_registers section."""
        yaml_content = """
other_section:
  foo: bar
"""

        with TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / 'test_config.yaml'
            with open(yaml_path, 'w') as f:
                f.write(yaml_content)

            with pytest.raises(ValueError, match="must contain 'bad_registers'"):
                BADRegisterMapper.from_yaml(yaml_path)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_single_register(self):
        """Test mapping a single register."""
        mapper = BADRegisterMapper(
            registers=[
                BADRegisterConfig(name="solo", datatype=BasicAppDataTypes.BOOLEAN)
            ]
        )

        mappings = mapper.to_register_mappings()
        assert len(mappings) == 1
        assert mappings[0].cr_number == 6

    def test_all_strategies_produce_valid_mappings(self):
        """Test that all strategies work and produce valid results."""
        registers = [
            BADRegisterConfig(name="a", datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),
            BADRegisterConfig(name="b", datatype=BasicAppDataTypes.PULSE_DURATION_NS_U8),
            BADRegisterConfig(name="c", datatype=BasicAppDataTypes.BOOLEAN),
        ]

        for strategy in ["first_fit", "best_fit", "type_clustering"]:
            mapper = BADRegisterMapper(registers=registers, strategy=strategy)
            mappings = mapper.to_register_mappings()

            # All should produce valid mappings
            assert len(mappings) == 3
            assert all(6 <= m.cr_number <= 17 for m in mappings)
            assert all(m.bit_slice[0] >= m.bit_slice[1] for m in mappings)

    def test_max_registers(self):
        """Test packing many registers (stress test)."""
        # Create 50 boolean registers (should fit in 2 CRs)
        registers = [
            BADRegisterConfig(name=f"bool_{i}", datatype=BasicAppDataTypes.BOOLEAN)
            for i in range(50)
        ]

        mapper = BADRegisterMapper(registers=registers, strategy="best_fit")
        report = mapper.generate_report()

        # 50 bits = 2 registers (32 + 18)
        assert len(report.register_map) == 2
        assert report.total_bits_used == 50
