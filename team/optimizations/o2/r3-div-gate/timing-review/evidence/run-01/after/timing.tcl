fconfigure stdout -buffering line
read_liberty /home/riscv/riscv-lab/o4-cost-20261020/library/NangateOpenCellLibrary_typical.lib
set_cmd_units -time ns -capacitance fF
set_wire_load_mode top
set_wire_load_model -name 5K_hvratio_1_1
read_verilog /home/riscv/riscv-lab/o2-r3-div-gate-cost-20261025/parent-sta-01/sta-canonical.v
link_design CommonParentCostTop
set inputs {}
foreach p [all_inputs] {if {[get_full_name $p] ne "clock"} {lappend inputs $p}}
set outputs [all_outputs]
create_clock -name core_clk -period 1.0 [get_ports clock]
set_clock_uncertainty 0.05 [get_clocks core_clk]
set_clock_transition 0.05 [get_clocks core_clk]
set_input_delay -max 0.1 -clock core_clk $inputs
set_output_delay -max 0.1 -clock core_clk $outputs
set_input_transition 0.05 $inputs
set_load 5 $outputs
puts "O4_CMD_UNITS time=ns capacitance=fF (explicit set_cmd_units accepted)"
puts "O4_CONSTRAINED_INPUT_BITS [llength $inputs]"
puts "O4_CONSTRAINED_OUTPUT_BITS [llength $outputs]"
puts "O4_REGISTER_CELLS [llength [all_registers -cells]]"
set_case_analysis 0 [get_ports testEnable]
report_clock_properties [get_clocks core_clk]
set q [all_registers -output_pins]
set d [all_registers -data_pins]
report_checks -from $q -to [get_pins {c197351/D}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-r3-div-gate-timing-review-20261025/run-01/after/float_hold_regs.rpt
report_checks -from $inputs -to [get_pins {c197351/D}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-r3-div-gate-timing-review-20261025/run-01/after/float_hold_inputs.rpt
report_checks -from [get_ports {io_flush*}] -to [get_pins {c197351/D}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-r3-div-gate-timing-review-20261025/run-01/after/float_hold_flush.rpt
report_checks -from $q -to [get_pins {c197350/D}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-r3-div-gate-timing-review-20261025/run-01/after/int_hold_regs.rpt
report_checks -from $inputs -to [get_pins {c197350/D}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-r3-div-gate-timing-review-20261025/run-01/after/int_hold_inputs.rpt
report_checks -from [get_ports {io_flush*}] -to [get_pins {c197350/D}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-r3-div-gate-timing-review-20261025/run-01/after/int_hold_flush.rpt
report_checks -from $q -to [get_pins {c197349/D}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-r3-div-gate-timing-review-20261025/run-01/after/div_busy_regs.rpt
report_checks -from $inputs -to [get_pins {c197349/D}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-r3-div-gate-timing-review-20261025/run-01/after/div_busy_inputs.rpt
report_checks -from [get_ports {io_flush*}] -to [get_pins {c197349/D}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-r3-div-gate-timing-review-20261025/run-01/after/div_busy_flush.rpt
report_checks -to [get_pins {c203017/E}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-r3-div-gate-timing-review-20261025/run-01/after/icg0_all.rpt
report_checks -from [get_pins {c197351/Q}] -to [get_pins {c203017/E}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-r3-div-gate-timing-review-20261025/run-01/after/icg0_hold.rpt
report_checks -to [get_pins {c203018/E}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-r3-div-gate-timing-review-20261025/run-01/after/icg1_all.rpt
report_checks -from [get_pins {c197350/Q}] -to [get_pins {c203018/E}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-r3-div-gate-timing-review-20261025/run-01/after/icg1_hold.rpt
report_checks -to [get_pins {c203019/E}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-r3-div-gate-timing-review-20261025/run-01/after/icg2_all.rpt
report_checks -from [get_pins {c201450/Q}] -to [get_pins {c201635/D}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-r3-div-gate-timing-review-20261025/run-01/after/fixed_before_r2r.rpt
report_checks -from [get_ports {io_in_bits_vpu_vsew[0]}] -to [get_pins {c201635/D}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-r3-div-gate-timing-review-20261025/run-01/after/fixed_before_i2r.rpt
report_checks -from [get_pins {c201450/Q}] -to [get_pins {c201635/D}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-r3-div-gate-timing-review-20261025/run-01/after/fixed_after_r2r.rpt
report_checks -from [get_ports {io_in_bits_src_0[71]}] -to [get_pins {c201635/D}] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/riscv/riscv-lab/o2-r3-div-gate-timing-review-20261025/run-01/after/fixed_after_i2r.rpt
puts "R3_TARGETED_STA_COMPLETE"
exit
