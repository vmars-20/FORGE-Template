"""
Unit tests for BasicAppsRegPackage (Phase 3).

Tests:
- DataTypeSpec validation
- BasicAppsRegPackage validation
- YAML serialization/deserialization
- Control register export
- Integration with MokuConfig
"""

import pytest
from pathlib import Path
from forge_codegen.basic_serialized_datatypes import BasicAppDataTypes
from forge_codegen.models.package import DataTypeSpec, BasicAppsRegPackage


class TestDataTypeSpec:
    """Tests for DataTypeSpec validation."""

    def test_valid_datatype_spec(self):
        """Test creating a valid DataTypeSpec."""
        dt = DataTypeSpec(
            name="intensity",
            datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
            description="Output voltage",
            default_value=2400,
            min_value=0,
            max_value=5000,
            display_name="Intensity",
            units="mV"
        )

        assert dt.name == "intensity"
        assert dt.datatype == BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16
        assert dt.default_value == 2400
        assert dt.units == "mV"

    def test_name_validation_must_start_with_letter(self):
        """Test name must start with letter."""
        with pytest.raises(ValueError, match="must start with letter"):
            DataTypeSpec(
                name="123_invalid",
                datatype=BasicAppDataTypes.BOOLEAN
            )

    def test_name_validation_reserved_word(self):
        """Test name cannot be VHDL reserved word."""
        with pytest.raises(ValueError, match="reserved word"):
            DataTypeSpec(
                name="signal",
                datatype=BasicAppDataTypes.BOOLEAN
            )

    def test_default_value_type_mismatch(self):
        """Test default_value must match type (bool vs int)."""
        with pytest.raises(ValueError, match="bool default_value"):
            DataTypeSpec(
                name="enable",
                datatype=BasicAppDataTypes.BOOLEAN,
                default_value=1  # Should be bool, not int
            )

    def test_default_value_out_of_range(self):
        """Test default_value must be within type range."""
        with pytest.raises(ValueError, match="above max"):
            DataTypeSpec(
                name="voltage",
                datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
                default_value=100000  # Exceeds max for voltage type
            )

    def test_min_max_validation(self):
        """Test min_value must be <= max_value."""
        with pytest.raises(ValueError, match="cannot be greater than"):
            DataTypeSpec(
                name="counter",
                datatype=BasicAppDataTypes.PULSE_DURATION_MS_U16,
                min_value=100,
                max_value=50  # Invalid: min > max
            )

    def test_ui_constraint_exceeds_type_limit(self):
        """Test UI constraints must be within type limits (strict validation)."""
        with pytest.raises(ValueError, match="above type maximum"):
            DataTypeSpec(
                name="voltage",
                datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,  # ±5000mV limit
                default_value=3000,
                max_value=10000  # Exceeds type limit
            )

    def test_to_bad_register_config(self):
        """Test conversion to BADRegisterConfig."""
        dt = DataTypeSpec(
            name="intensity",
            datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
            description="Output voltage",
            default_value=2400
        )

        config = dt.to_bad_register_config()

        assert config.name == "intensity"
        assert config.datatype == BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16
        assert config.default_value == 2400


class TestBasicAppsRegPackage:
    """Tests for BasicAppsRegPackage."""

    def test_valid_package(self):
        """Test creating a valid package."""
        package = BasicAppsRegPackage(
            app_name="TestApp",
            description="Test application",
            datatypes=[
                DataTypeSpec(
                    name="enable",
                    datatype=BasicAppDataTypes.BOOLEAN,
                    default_value=False
                ),
                DataTypeSpec(
                    name="voltage",
                    datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
                    default_value=2400
                )
            ]
        )

        assert package.app_name == "TestApp"
        assert len(package.datatypes) == 2
        assert package.mapping_strategy == "best_fit"

    def test_duplicate_names_rejected(self):
        """Test duplicate datatype names are rejected."""
        with pytest.raises(ValueError, match="Duplicate datatype names"):
            BasicAppsRegPackage(
                app_name="TestApp",
                datatypes=[
                    DataTypeSpec(name="voltage", datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),
                    DataTypeSpec(name="voltage", datatype=BasicAppDataTypes.VOLTAGE_INPUT_20V_S16),
                ]
            )

    def test_total_bits_overflow(self):
        """Test validation of 384-bit limit."""
        # Create 25 x 16-bit types (400 bits > 384 limit)
        datatypes = [
            DataTypeSpec(
                name=f"type_{i}",
                datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16
            )
            for i in range(25)  # 25 * 16 = 400 bits
        ]

        with pytest.raises(ValueError, match="exceeds 384-bit limit"):
            BasicAppsRegPackage(
                app_name="OverflowTest",
                datatypes=datatypes
            )

    def test_generate_mapping(self):
        """Test register mapping generation."""
        package = BasicAppsRegPackage(
            app_name="TestApp",
            datatypes=[
                DataTypeSpec(name="enable", datatype=BasicAppDataTypes.BOOLEAN),
                DataTypeSpec(name="timeout", datatype=BasicAppDataTypes.PULSE_DURATION_MS_U16),
                DataTypeSpec(name="voltage", datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16),
            ]
        )

        mappings = package.generate_mapping()

        assert len(mappings) == 3
        assert all(6 <= m.cr_number <= 17 for m in mappings)

    def test_to_control_registers(self):
        """Test export to MokuConfig format."""
        package = BasicAppsRegPackage(
            app_name="TestApp",
            datatypes=[
                DataTypeSpec(
                    name="enable",
                    datatype=BasicAppDataTypes.BOOLEAN,
                    default_value=True
                ),
                DataTypeSpec(
                    name="timeout",
                    datatype=BasicAppDataTypes.PULSE_DURATION_MS_U16,
                    default_value=1000
                ),
            ]
        )

        control_regs = package.to_control_registers()

        # Should have at least one CR
        assert len(control_regs) > 0

        # All CR numbers should be in valid range
        assert all(6 <= cr <= 17 for cr in control_regs.keys())

        # All values should be 32-bit integers
        assert all(0 <= val <= 0xFFFFFFFF for val in control_regs.values())

    def test_convert_to_raw_boolean(self):
        """Test boolean conversion."""
        package = BasicAppsRegPackage(
            app_name="TestApp",
            datatypes=[
                DataTypeSpec(
                    name="enable",
                    datatype=BasicAppDataTypes.BOOLEAN,
                    default_value=True
                )
            ]
        )

        dt_spec = package.datatypes[0]
        raw = package._convert_to_raw(dt_spec)
        assert raw == 1

    def test_convert_to_raw_voltage(self):
        """Test voltage conversion using TypeConverter."""
        package = BasicAppsRegPackage(
            app_name="TestApp",
            datatypes=[
                DataTypeSpec(
                    name="intensity",
                    datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
                    default_value=2400  # 2.4V
                )
            ]
        )

        dt_spec = package.datatypes[0]
        raw = package._convert_to_raw(dt_spec)

        # Should be non-zero and within 16-bit signed range
        assert raw != 0
        assert -32768 <= raw <= 32767

    def test_convert_to_raw_time(self):
        """Test time conversion (pass-through)."""
        package = BasicAppsRegPackage(
            app_name="TestApp",
            datatypes=[
                DataTypeSpec(
                    name="duration",
                    datatype=BasicAppDataTypes.PULSE_DURATION_NS_U8,
                    default_value=128
                )
            ]
        )

        dt_spec = package.datatypes[0]
        raw = package._convert_to_raw(dt_spec)
        assert raw == 128  # Pass through unchanged

    def test_yaml_roundtrip(self, tmp_path):
        """Test YAML serialization and deserialization."""
        original = BasicAppsRegPackage(
            app_name="TestApp",
            description="Test application",
            datatypes=[
                DataTypeSpec(
                    name="intensity",
                    datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
                    description="Output voltage",
                    default_value=2400,
                    display_name="Intensity",
                    units="mV"
                )
            ],
            mapping_strategy="best_fit"
        )

        # Save to YAML
        yaml_path = tmp_path / "test.yaml"
        original.to_yaml(yaml_path)

        # Load from YAML
        loaded = BasicAppsRegPackage.from_yaml(yaml_path)

        # Compare
        assert loaded.app_name == original.app_name
        assert loaded.description == original.description
        assert len(loaded.datatypes) == len(original.datatypes)
        assert loaded.datatypes[0].name == original.datatypes[0].name
        assert loaded.datatypes[0].datatype == original.datatypes[0].datatype
        assert loaded.mapping_strategy == original.mapping_strategy

    def test_yaml_omits_none_fields(self, tmp_path):
        """Test YAML serialization omits None fields for cleaner output."""
        package = BasicAppsRegPackage(
            app_name="TestApp",
            datatypes=[
                DataTypeSpec(
                    name="enable",
                    datatype=BasicAppDataTypes.BOOLEAN,
                    default_value=False
                    # No min_value, max_value, display_name, units
                )
            ]
        )

        yaml_path = tmp_path / "test.yaml"
        package.to_yaml(yaml_path)

        # Read back and check that None fields are not present
        with open(yaml_path) as f:
            content = f.read()

        assert 'min_value: null' not in content
        assert 'max_value: null' not in content
        assert 'display_name: null' not in content
        assert 'units: null' not in content


class TestMokuConfigIntegration:
    """Test integration with moku-models."""

    def test_control_registers_compatible_with_moku_config(self):
        """Test control_registers export is MokuConfig-compatible."""
        from moku_models import MokuConfig, SlotConfig, MOKU_GO_PLATFORM

        # Create package
        package = BasicAppsRegPackage(
            app_name="TestApp",
            datatypes=[
                DataTypeSpec(
                    name="enable",
                    datatype=BasicAppDataTypes.BOOLEAN,
                    default_value=True
                )
            ]
        )

        # Export control registers
        control_regs = package.to_control_registers()

        # Create MokuConfig with exported values
        config = MokuConfig(
            platform=MOKU_GO_PLATFORM,
            slots={
                1: SlotConfig(
                    instrument='CloudCompile',
                    bitstream='test.tar',
                    control_registers=control_regs  # ← Should work!
                )
            }
        )

        # Validate
        assert config.slots[1].control_registers is not None
        assert len(config.slots[1].control_registers) == len(control_regs)

    def test_ds1140_pd_example_loads(self):
        """Test DS1140_PD example YAML loads successfully."""
        example_path = Path(__file__).parent.parent / "examples" / "DS1140_PD_interface.yaml"

        if not example_path.exists():
            pytest.skip("DS1140_PD_interface.yaml not found")

        # Load example
        package = BasicAppsRegPackage.from_yaml(example_path)

        # Validate
        assert package.app_name == "DS1140_PD"
        assert len(package.datatypes) == 8  # 3 booleans + 3 timers + 2 voltages
        assert package.mapping_strategy == "best_fit"

        # Generate mapping
        mappings = package.generate_mapping()
        assert len(mappings) == 8

        # Export control registers
        control_regs = package.to_control_registers()
        assert len(control_regs) > 0

    def test_ds1140_pd_deployment_example_runs(self):
        """Test DS1140_PD deployment example runs without errors."""
        example_path = Path(__file__).parent.parent / "examples" / "DS1140_PD_interface.yaml"

        if not example_path.exists():
            pytest.skip("DS1140_PD_interface.yaml not found")

        from moku_models import MokuConfig, SlotConfig, MokuConnection, MOKU_GO_PLATFORM

        # Load and process (simulating deployment example)
        reg_interface = BasicAppsRegPackage.from_yaml(example_path)
        mappings = reg_interface.generate_mapping()
        control_regs = reg_interface.to_control_registers()

        # Create MokuConfig
        config = MokuConfig(
            platform=MOKU_GO_PLATFORM,
            slots={
                1: SlotConfig(
                    instrument='CloudCompile',
                    bitstream='test.tar',
                    control_registers=control_regs
                )
            },
            routing=[]
        )

        # Validate
        assert config.slots[1].control_registers is not None
        assert len(config.slots[1].control_registers) == len(control_regs)


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_default_value(self):
        """Test datatype with no default value."""
        package = BasicAppsRegPackage(
            app_name="TestApp",
            datatypes=[
                DataTypeSpec(
                    name="enable",
                    datatype=BasicAppDataTypes.BOOLEAN
                    # No default_value
                )
            ]
        )

        control_regs = package.to_control_registers()

        # Should handle None default gracefully (no register entry)
        # or register with 0 value
        assert isinstance(control_regs, dict)

    def test_mapping_cache_works(self):
        """Test mapping cache avoids recomputation."""
        package = BasicAppsRegPackage(
            app_name="TestApp",
            datatypes=[
                DataTypeSpec(name="enable", datatype=BasicAppDataTypes.BOOLEAN)
            ]
        )

        # First call
        mappings1 = package.generate_mapping()

        # Second call (should use cache)
        mappings2 = package.generate_mapping()

        # Should be same object reference (cached)
        assert mappings1 is mappings2

    def test_all_strategies_work(self):
        """Test all mapping strategies work."""
        datatypes = [
            DataTypeSpec(name="enable", datatype=BasicAppDataTypes.BOOLEAN, default_value=False),
            DataTypeSpec(name="voltage", datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16, default_value=2400),
            DataTypeSpec(name="timeout", datatype=BasicAppDataTypes.PULSE_DURATION_MS_U16, default_value=1000),
        ]

        for strategy in ["first_fit", "best_fit", "type_clustering"]:
            package = BasicAppsRegPackage(
                app_name="TestApp",
                datatypes=datatypes,
                mapping_strategy=strategy
            )

            mappings = package.generate_mapping()
            assert len(mappings) == 3

            control_regs = package.to_control_registers()
            assert len(control_regs) > 0
