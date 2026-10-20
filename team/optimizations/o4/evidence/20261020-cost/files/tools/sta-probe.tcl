read_liberty /home/riscv/riscv-lab/o4-cost-20261020/library/NangateOpenCellLibrary_typical.lib
set_cmd_units -time ns -capacitance fF
read_verilog /home/riscv/riscv-lab/o4-cost-20261020/o1-fu-map-02/mapped.v
link_design CommonFuCostTop
puts "O4_PORTS [llength [get_ports *]]"
puts "O4_CLOCK [get_full_name [get_ports clock]]"
puts "O4_INBUS [llength [get_ports io_in_bits_ctrl_robIdx_value*]]"
puts "O4_FFS [llength [all_registers -cells]]"
puts "O4_D [llength [all_registers -data_pins]]"
puts "O4_Q [llength [all_registers -output_pins]]"
puts "O4_INPUTS [llength [all_inputs]]"
puts "O4_OUTPUTS [llength [all_outputs]]"
puts O4_PROBE_COMPLETE
exit
