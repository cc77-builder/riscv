#pragma once
#include <cstdint>
#include "verilated.h"
// Port declaration stub ONLY: no DUT behavior and no linkable simulation model.
class VVDotFuTestTop { public:
 explicit VVDotFuTestTop(VerilatedContext*);
 void eval(); void final();
 uint32_t clock{},reset{};
 uint32_t io_in_valid{};
 uint32_t io_out_ready{};
 uint32_t io_vl{};
 uint32_t io_ctrl_vl{};
 uint32_t io_vsew{};
 uint32_t io_vlmul{};
 uint32_t io_vstart{};
 uint32_t io_vill{};
 uint32_t io_vm{};
 uint32_t io_vta{};
 uint32_t io_vma{};
 uint32_t io_vxrm{};
 uint32_t io_op{};
 uint32_t io_rob_flag{};
 uint32_t io_rob_value{};
 uint32_t io_pdest{};
 uint32_t io_write_v0{};
 uint32_t io_flush_valid{};
 uint32_t io_flush_flag{};
 uint32_t io_flush_value{};
 uint32_t io_flush_self{};
 uint32_t io_out_valid{};
 uint32_t io_in_ready{};
 uint32_t io_out_pdest{};
 uint32_t io_out_rob_flag{};
 uint32_t io_out_rob_value{};
 uint32_t io_out_exception{};
 uint32_t io_out_vec_wen{};
 uint32_t io_out_v0_wen{};
 uint32_t io_out_ctrl{};
 uint64_t io_perf_tag{};
 uint64_t io_out_perf_tag{};
 uint64_t io_out_rename_tag{};
 uint32_t io_vs1[4]{};
 uint32_t io_vs2[4]{};
 uint32_t io_old_vd[4]{};
 uint32_t io_mask[4]{};
 uint32_t io_result[4]{};
};
