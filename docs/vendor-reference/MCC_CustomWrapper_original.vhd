library IEEE;
use IEEE.Std_Logic_1164.all;
use IEEE.Numeric_Std.all;

use WORK.InterlacingSupport.all;

entity CustomWrapper is
	port (
		Clk : in std_logic;
		Reset : in std_logic;
		Sync : in std_logic_vector(31 downto 0);

		InputA : in signed(15 downto 0);
		InputB : in signed(15 downto 0);
		InputC : in signed(15 downto 0);
		InputD : in signed(15 downto 0);

		ExtTrig : in std_logic;

		OutputA : out signed(15 downto 0);
		OutputB : out signed(15 downto 0);
		OutputC : out signed(15 downto 0);
		OutputD : out signed(15 downto 0);

		Control0 : in std_logic_vector(31 downto 0);
		Control1 : in std_logic_vector(31 downto 0);
		Control2 : in std_logic_vector(31 downto 0);
		Control3 : in std_logic_vector(31 downto 0);
		Control4 : in std_logic_vector(31 downto 0);
		Control5 : in std_logic_vector(31 downto 0);
		Control6 : in std_logic_vector(31 downto 0);
		Control7 : in std_logic_vector(31 downto 0);
		Control8 : in std_logic_vector(31 downto 0);
		Control9 : in std_logic_vector(31 downto 0);
		Control10 : in std_logic_vector(31 downto 0);
		Control11 : in std_logic_vector(31 downto 0);
		Control12 : in std_logic_vector(31 downto 0);
		Control13 : in std_logic_vector(31 downto 0);
		Control14 : in std_logic_vector(31 downto 0);
		Control15 : in std_logic_vector(31 downto 0);

		Status0 : out std_logic_vector(31 downto 0);
		Status1 : out std_logic_vector(31 downto 0);
		Status2 : out std_logic_vector(31 downto 0);
		Status3 : out std_logic_vector(31 downto 0);
		Status4 : out std_logic_vector(31 downto 0);
		Status5 : out std_logic_vector(31 downto 0);
		Status6 : out std_logic_vector(31 downto 0);
		Status7 : out std_logic_vector(31 downto 0);
		Status8 : out std_logic_vector(31 downto 0);
		Status9 : out std_logic_vector(31 downto 0);
		Status10 : out std_logic_vector(31 downto 0);
		Status11 : out std_logic_vector(31 downto 0);
		Status12 : out std_logic_vector(31 downto 0);
		Status13 : out std_logic_vector(31 downto 0);
		Status14 : out std_logic_vector(31 downto 0);
		Status15 : out std_logic_vector(31 downto 0)
	);
end entity;


entity CustomWrapperInterlaced is
	generic (
		IN_LANES : integer;
		OUT_LANES : integer
	);
	port (
		Clk : in std_logic;
		Reset : in std_logic;
		Sync : in std_logic_vector(31 downto 0);

		InputA : in ArrayOfSigned(0 to IN_LANES - 1)(15 downto 0);
		InputB : in ArrayOfSigned(0 to IN_LANES - 1)(15 downto 0);
		InputC : in ArrayOfSigned(0 to IN_LANES - 1)(15 downto 0);
		InputD : in ArrayOfSigned(0 to IN_LANES - 1)(15 downto 0);

		ExtTrig : in std_logic_vector(0 to IN_LANES - 1);

		OutputA : out ArrayOfSigned(0 to OUT_LANES - 1)(15 downto 0);
		OutputB : out ArrayOfSigned(0 to OUT_LANES - 1)(15 downto 0);
		OutputC : out ArrayOfSigned(0 to OUT_LANES - 1)(15 downto 0);
		OutputD : out ArrayOfSigned(0 to OUT_LANES - 1)(15 downto 0);

		Control0 : in std_logic_vector(31 downto 0);
		Control1 : in std_logic_vector(31 downto 0);
		Control2 : in std_logic_vector(31 downto 0);
		Control3 : in std_logic_vector(31 downto 0);
		Control4 : in std_logic_vector(31 downto 0);
		Control5 : in std_logic_vector(31 downto 0);
		Control6 : in std_logic_vector(31 downto 0);
		Control7 : in std_logic_vector(31 downto 0);
		Control8 : in std_logic_vector(31 downto 0);
		Control9 : in std_logic_vector(31 downto 0);
		Control10 : in std_logic_vector(31 downto 0);
		Control11 : in std_logic_vector(31 downto 0);
		Control12 : in std_logic_vector(31 downto 0);
		Control13 : in std_logic_vector(31 downto 0);
		Control14 : in std_logic_vector(31 downto 0);
		Control15 : in std_logic_vector(31 downto 0);

		Status0 : out std_logic_vector(31 downto 0);
		Status1 : out std_logic_vector(31 downto 0);
		Status2 : out std_logic_vector(31 downto 0);
		Status3 : out std_logic_vector(31 downto 0);
		Status4 : out std_logic_vector(31 downto 0);
		Status5 : out std_logic_vector(31 downto 0);
		Status6 : out std_logic_vector(31 downto 0);
		Status7 : out std_logic_vector(31 downto 0);
		Status8 : out std_logic_vector(31 downto 0);
		Status9 : out std_logic_vector(31 downto 0);
		Status10 : out std_logic_vector(31 downto 0);
		Status11 : out std_logic_vector(31 downto 0);
		Status12 : out std_logic_vector(31 downto 0);
		Status13 : out std_logic_vector(31 downto 0);
		Status14 : out std_logic_vector(31 downto 0);
		Status15 : out std_logic_vector(31 downto 0)
	);
end entity;
