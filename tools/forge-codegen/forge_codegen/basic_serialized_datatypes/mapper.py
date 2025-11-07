"""
Register mapping algorithm for BasicAppDataTypes.

This module provides pure Python algorithms for mapping BasicAppDataTypes to
physical Control Registers (CR6-CR17) with efficient bit packing.

Architecture:
- Zero dependencies (pure Python + stdlib only)
- No Pydantic, no YAML parsing
- Reusable across projects
- Travels with basic-app-datatypes package

Design References:
- Spec: docs/BasicAppDataTypes/BAD_Phase2_RegisterMapping.md
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional, Literal
from enum import Enum
from .types import BasicAppDataTypes
from .metadata import TYPE_REGISTRY


@dataclass(frozen=True)
class RegisterMapping:
    """
    Result of mapping a BasicAppDataType to physical registers (pure data).

    Attributes:
        name: User-defined name for this instance (e.g., "intensity", "threshold")
        datatype: The BasicAppDataTypes enum value
        cr_number: Control register number (6-17)
        bit_slice: Tuple of (msb, lsb) for VHDL extraction (e.g., (31, 16))

    Example:
        RegisterMapping(
            name="intensity",
            datatype=BasicAppDataTypes.VOLTAGE_OUTPUT_05V_S16,
            cr_number=6,
            bit_slice=(31, 16)
        )
        # Generates VHDL: app_reg_6(31 downto 16)
    """
    name: str
    datatype: BasicAppDataTypes
    cr_number: int  # 6-17
    bit_slice: Tuple[int, int]  # (msb, lsb)

    def to_vhdl_slice(self) -> str:
        """
        Generate VHDL bit extraction code.

        Returns:
            VHDL slice syntax (e.g., "app_reg_6(31 downto 16)" or "app_reg_6(15)")
        """
        msb, lsb = self.bit_slice
        if msb == lsb:
            # Single bit
            return f"app_reg_{self.cr_number}({msb})"
        else:
            # Multi-bit slice
            return f"app_reg_{self.cr_number}({msb} downto {lsb})"

    def bit_width(self) -> int:
        """Calculate bit width from slice."""
        return self.bit_slice[0] - self.bit_slice[1] + 1


@dataclass
class MappingReport:
    """
    Detailed report of register mapping results.

    Attributes:
        mappings: List of RegisterMapping objects
        total_bits_used: Total bits consumed across all mappings
        total_bits_available: Total bits available (384 = 12 * 32)
        efficiency_percent: Percentage of bits used
        register_map: Dictionary mapping CR number to list of RegisterMappings
    """
    mappings: List[RegisterMapping]
    total_bits_used: int
    total_bits_available: int = 384  # 12 registers * 32 bits
    efficiency_percent: float = field(init=False)
    register_map: Dict[int, List[RegisterMapping]] = field(init=False)

    def __post_init__(self):
        """Calculate derived fields."""
        self.efficiency_percent = (self.total_bits_used / self.total_bits_available) * 100

        # Build register map
        self.register_map = {}
        for mapping in self.mappings:
            if mapping.cr_number not in self.register_map:
                self.register_map[mapping.cr_number] = []
            self.register_map[mapping.cr_number].append(mapping)

    def to_ascii_art(self) -> str:
        """
        Generate ASCII art visualization of register packing.

        Example:
            CR6  [31:16] intensity (16-bit) | [15:0] threshold (16-bit)
            CR7  [31:24] clock_div (8-bit)  | [23:0] UNUSED
        """
        lines = []
        lines.append("=" * 80)
        lines.append("REGISTER MAPPING VISUALIZATION")
        lines.append("=" * 80)

        for cr_num in sorted(self.register_map.keys()):
            parts = []
            for mapping in sorted(self.register_map[cr_num],
                                 key=lambda m: m.bit_slice[0],
                                 reverse=True):
                msb, lsb = mapping.bit_slice
                width = mapping.bit_width()
                parts.append(f"[{msb}:{lsb}] {mapping.name} ({width}-bit)")

            lines.append(f"CR{cr_num:2d}  " + " | ".join(parts))

        # Show unused registers
        all_crs = set(range(6, 18))
        used_crs = set(self.register_map.keys())
        unused_crs = all_crs - used_crs
        if unused_crs:
            for cr_num in sorted(unused_crs):
                lines.append(f"CR{cr_num:2d}  [31:0] UNUSED")

        lines.append("=" * 80)
        lines.append(f"Efficiency: {self.total_bits_used}/{self.total_bits_available} bits ({self.efficiency_percent:.2f}%)")
        lines.append(f"Registers used: {len(self.register_map)}/12")
        lines.append("=" * 80)

        return "\n".join(lines)

    def to_markdown(self) -> str:
        """
        Generate Markdown table of register mappings.

        Returns:
            Markdown table with columns: CR | Bit Slice | Name | Type | Width
        """
        lines = []
        lines.append("# Register Mapping Report")
        lines.append("")
        lines.append("| CR  | Bit Slice | Name | Type | Width |")
        lines.append("|-----|-----------|------|------|-------|")

        for mapping in sorted(self.mappings,
                            key=lambda m: (m.cr_number, -m.bit_slice[0])):
            msb, lsb = mapping.bit_slice
            width = mapping.bit_width()
            type_name = mapping.datatype.value
            lines.append(f"| {mapping.cr_number:2d}  | {msb:2d}:{lsb:2d}     | {mapping.name} | {type_name} | {width} |")

        lines.append("")
        lines.append("## Summary")
        lines.append(f"- **Total bits used**: {self.total_bits_used}/{self.total_bits_available}")
        lines.append(f"- **Efficiency**: {self.efficiency_percent:.2f}%")
        lines.append(f"- **Registers used**: {len(self.register_map)}/12")

        return "\n".join(lines)

    def to_vhdl_comments(self) -> str:
        """
        Generate VHDL comment block documenting mapping.

        Returns:
            VHDL comments suitable for code generation
        """
        lines = []
        lines.append("--------------------------------------------------------------------------------")
        lines.append("-- AUTO-GENERATED REGISTER MAPPING")
        lines.append("-- Generated by BasicAppDataTypes RegisterMapper")
        lines.append("--------------------------------------------------------------------------------")

        for cr_num in sorted(self.register_map.keys()):
            lines.append(f"--")
            lines.append(f"-- CR{cr_num}:")
            for mapping in sorted(self.register_map[cr_num],
                                 key=lambda m: m.bit_slice[0],
                                 reverse=True):
                msb, lsb = mapping.bit_slice
                type_name = mapping.datatype.value
                lines.append(f"--   [{msb:2d}:{lsb:2d}] {mapping.name} ({type_name}, {mapping.bit_width()}-bit)")

        lines.append("--")
        lines.append(f"-- Total: {self.total_bits_used}/{self.total_bits_available} bits ({self.efficiency_percent:.2f}%)")
        lines.append("--------------------------------------------------------------------------------")

        return "\n".join(lines)

    def to_json(self) -> Dict:
        """
        Generate JSON-serializable dictionary (primary on-disk format).

        Returns:
            Dictionary suitable for json.dumps()
        """
        return {
            "mappings": [
                {
                    "name": m.name,
                    "datatype": m.datatype.value,
                    "cr_number": m.cr_number,
                    "bit_slice": list(m.bit_slice)
                }
                for m in self.mappings
            ],
            "summary": {
                "bits_used": self.total_bits_used,
                "bits_available": self.total_bits_available,
                "efficiency_percent": round(self.efficiency_percent, 2),
                "registers_used": len(self.register_map)
            }
        }


class RegisterMapper:
    """
    Pure algorithm: Maps BasicAppDataTypes to Control Registers.

    Supports multiple packing strategies:
    - first_fit: Sequential packing (simple, predictable)
    - best_fit: Size-sorted packing (optimal efficiency)
    - type_clustering: Group by type family (readable)

    Constraints:
    - 12 registers available (CR6-CR17)
    - 32 bits per register
    - 384 total bits
    - MSB-first packing within registers
    - No spanning across registers (Phase 2 limitation)
    """

    MAX_APP_REGISTERS = 12  # CR6-CR17
    BITS_PER_REGISTER = 32
    TOTAL_BITS = MAX_APP_REGISTERS * BITS_PER_REGISTER  # 384 bits
    FIRST_CR = 6
    LAST_CR = 17

    def map(self,
            items: List[Tuple[str, BasicAppDataTypes]],
            strategy: Literal["first_fit", "best_fit", "type_clustering"] = "best_fit"
            ) -> List[RegisterMapping]:
        """
        Map datatypes to control registers (pure function).

        Args:
            items: List of (name, BasicAppDataTypes) tuples
            strategy: Packing strategy ('first_fit', 'best_fit', 'type_clustering')

        Returns:
            List of RegisterMapping objects

        Raises:
            ValueError: If types don't fit in 384 bits or invalid inputs
        """
        # Validation
        if not items:
            return []

        # Check for duplicate names
        names = [name for name, _ in items]
        if len(names) != len(set(names)):
            duplicates = [name for name in names if names.count(name) > 1]
            raise ValueError(f"Duplicate names found: {set(duplicates)}")

        # Calculate total bits needed
        total_bits = sum(TYPE_REGISTRY[dtype].bit_width for _, dtype in items)
        if total_bits > self.TOTAL_BITS:
            raise ValueError(
                f"Cannot fit {total_bits} bits into {self.TOTAL_BITS} available bits "
                f"({total_bits - self.TOTAL_BITS} bits overflow)"
            )

        # Check for types >32 bits (Phase 2 limitation)
        for name, dtype in items:
            metadata = TYPE_REGISTRY[dtype]
            if metadata.bit_width > self.BITS_PER_REGISTER:
                raise ValueError(
                    f"Type '{name}' ({dtype.value}) is {metadata.bit_width} bits, "
                    f"exceeds {self.BITS_PER_REGISTER}-bit register limit (Phase 2 limitation)"
                )

        # Route to appropriate strategy
        if strategy == "first_fit":
            return self._first_fit(items)
        elif strategy == "best_fit":
            return self._best_fit(items)
        elif strategy == "type_clustering":
            return self._type_clustering(items)
        else:
            raise ValueError(f"Unknown packing strategy: {strategy}")

    def _first_fit(self, items: List[Tuple[str, BasicAppDataTypes]]) -> List[RegisterMapping]:
        """
        First-fit packing: Sequential allocation from MSB.

        Algorithm:
        1. Start at CR6, bit position 31 (MSB)
        2. Pack each type sequentially
        3. Move to next register when current is full
        4. Simple and deterministic
        """
        mappings = []
        current_cr = self.FIRST_CR
        current_bit = self.BITS_PER_REGISTER - 1  # Start at MSB (31)

        for name, dtype in items:
            bit_width = TYPE_REGISTRY[dtype].bit_width

            # Check if we need to move to next register
            if current_bit + 1 < bit_width:
                # Not enough space in current register
                current_cr += 1
                current_bit = self.BITS_PER_REGISTER - 1

                if current_cr > self.LAST_CR:
                    raise ValueError("Ran out of registers (should not happen after validation)")

            # Pack this type
            msb = current_bit
            lsb = current_bit - bit_width + 1

            mappings.append(RegisterMapping(
                name=name,
                datatype=dtype,
                cr_number=current_cr,
                bit_slice=(msb, lsb)
            ))

            # Update current position
            current_bit = lsb - 1

        return mappings

    def _best_fit(self, items: List[Tuple[str, BasicAppDataTypes]]) -> List[RegisterMapping]:
        """
        Best-fit packing: Sort by size (largest first) for optimal packing.

        Algorithm:
        1. Sort types by bit width (descending)
        2. Use first-fit on sorted list
        3. Minimizes wasted space
        """
        # Sort by bit width (largest first), then by name for determinism
        sorted_items = sorted(items,
                            key=lambda x: (-TYPE_REGISTRY[x[1]].bit_width, x[0]))

        return self._first_fit(sorted_items)

    def _type_clustering(self, items: List[Tuple[str, BasicAppDataTypes]]) -> List[RegisterMapping]:
        """
        Type-clustering packing: Group by type family for readability.

        Algorithm:
        1. Group by category: voltage (output, input), time (ns, us, ms, s), boolean
        2. Within each group, sort by bit width (descending)
        3. Pack groups sequentially
        4. More readable but potentially less efficient
        """
        # Categorize types
        voltage_output = []
        voltage_input = []
        time_types = []
        booleans = []

        for name, dtype in items:
            metadata = TYPE_REGISTRY[dtype]

            if dtype == BasicAppDataTypes.BOOLEAN:
                booleans.append((name, dtype))
            elif metadata.direction == 'output':
                voltage_output.append((name, dtype))
            elif metadata.direction == 'input':
                voltage_input.append((name, dtype))
            elif metadata.unit in ('ns', 'us', 'ms', 's'):
                time_types.append((name, dtype))
            else:
                # Fallback
                time_types.append((name, dtype))

        # Sort each group by bit width (descending), then name
        def sort_key(x):
            return (-TYPE_REGISTRY[x[1]].bit_width, x[0])

        voltage_output.sort(key=sort_key)
        voltage_input.sort(key=sort_key)
        time_types.sort(key=sort_key)
        booleans.sort(key=lambda x: x[0])  # Just by name

        # Combine in logical order
        clustered_items = voltage_output + voltage_input + time_types + booleans

        return self._first_fit(clustered_items)

    def generate_report(self, mappings: List[RegisterMapping]) -> MappingReport:
        """
        Generate detailed mapping report.

        Args:
            mappings: List of RegisterMapping objects (from map())

        Returns:
            MappingReport with visualizations and statistics
        """
        total_bits = sum(m.bit_width() for m in mappings)
        return MappingReport(
            mappings=mappings,
            total_bits_used=total_bits,
            total_bits_available=self.TOTAL_BITS
        )
