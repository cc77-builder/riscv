fconfigure stdout -buffering line
read_liberty /home/lizufan/riscv-tools/nangate45/NangateOpenCellLibrary_typical.lib
set_cmd_units -time ns -capacitance fF
set_wire_load_mode top
set_wire_load_model -name 5K_hvratio_1_1
read_verilog /home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-fa-20261108-main/sta-resume-01/mapped.v
link_design CommonFuCostTop
set inputs {}
foreach p [all_inputs] {if {[get_full_name $p] ne "clock"} {lappend inputs $p}}
set outputs [all_outputs]
create_clock -name core_clk -period 1.0 [get_ports clock]
set_clock_uncertainty 0.05 [get_clocks core_clk]
set_clock_transition 0.05 [get_clocks core_clk]
set_input_delay -max 0.1 -clock core_clk $inputs
set_output_delay -max 0.1 -clock core_clk $outputs
set_input_transition 0.05 $inputs
set_load 5.0 $outputs
check_setup -verbose > /home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-fa-20261108-main/sta-resume-01/setup-checks.rpt
set q [all_registers -output_pins]
set d [all_registers -data_pins]
report_checks -from $q -to $d -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-fa-20261108-main/sta-resume-01/r2r.rpt
report_checks -from $inputs -to $d -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-fa-20261108-main/sta-resume-01/i2r.rpt
report_checks -from $q -to $outputs -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-fa-20261108-main/sta-resume-01/r2o.rpt
report_checks -from $inputs -to $outputs -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-fa-20261108-main/sta-resume-01/i2o.rpt
report_checks -from [get_ports io_out_ready] -to [get_ports io_in_ready] -path_delay max -group_count 1 -endpoint_count 1 -format full_clock_expanded -fields {capacitance slew input_pin net} -digits 6 -no_line_splits > /home/lizufan/riscv-lab/r5-firstdot-20261026-0056/runs/dot16-prefix-fa-20261108-main/sta-resume-01/ready.rpt
puts "DOT16_GENERATED_FU_STA_COMPLETE"
exit
