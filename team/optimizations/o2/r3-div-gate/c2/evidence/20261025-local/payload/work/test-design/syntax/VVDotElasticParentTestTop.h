// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Primary model header
//
// This header should be included by all source files instantiating the design.
// The class here is then constructed to instantiate the design.
// See the Verilator manual for examples.

#ifndef VERILATED_VVDOTELASTICPARENTTESTTOP_H_
#define VERILATED_VVDOTELASTICPARENTTESTTOP_H_  // guard

#include "verilated.h"

class VVDotElasticParentTestTop__Syms;
class VVDotElasticParentTestTop___024root;
class VVDotElasticParentTestTop_SRT16Divint;


// This class is the main interface to the Verilated model
class alignas(VL_CACHE_LINE_BYTES) VVDotElasticParentTestTop VL_NOT_FINAL : public VerilatedModel {
    friend class VVDotElasticParentTestTop__Syms;
  private:
    // Symbol table holding complete model state (owned by this class)
    VVDotElasticParentTestTop__Syms* const vlSymsp;
    // Evaluation loop
    VerilatedEvalLoop m_evalLoop;

  public:
    CData io_fp_lane_ready, io_fp_lane_finish, io_div_busy;

    // CONSTEXPR CAPABILITIES
    // Verilated with --trace?
    static constexpr bool traceCapable = false;

    // PORTS
    // The application code writes and reads these signals to
    // propagate new values into/out from the Verilated model.
    VL_IN8(&clock,0,0);
    VL_IN8(&reset,0,0);
    VL_IN8(&io_in_valid,0,0);
    VL_IN8(&io_out_ready,0,0);
    VL_IN8(&io_flush_valid,0,0);
    VL_IN8(&io_flush_flag,0,0);
    VL_IN8(&io_flush_self,0,0);
    VL_IN8(&io_test_enable,0,0);
    VL_OUT8(&io_in_ready,0,0);
    VL_OUT8(&io_out_valid,0,0);
    VL_IN8(&io_kind,1,0);
    VL_IN8(&io_vl,7,0);
    VL_IN8(&io_ctrl_vl,7,0);
    VL_IN8(&io_vsew,1,0);
    VL_IN8(&io_vlmul,2,0);
    VL_IN8(&io_vstart,7,0);
    VL_IN8(&io_vill,0,0);
    VL_IN8(&io_vm,0,0);
    VL_IN8(&io_vta,0,0);
    VL_IN8(&io_vma,0,0);
    VL_IN8(&io_vxrm,1,0);
    VL_IN8(&io_vuop_idx,6,0);
    VL_IN8(&io_frm,2,0);
    VL_IN8(&io_fp_rm,2,0);
    VL_IN8(&io_fp_wflags,0,0);
    VL_IN8(&io_rob_flag,0,0);
    VL_IN8(&io_rob_value,5,0);
    VL_IN8(&io_pdest,7,0);
    VL_IN8(&io_write_v0,0,0);
    VL_IN8(&io_flush_value,5,0);
    VL_OUT8(&io_out_rob_flag,0,0);
    VL_OUT8(&io_out_rob_value,5,0);
    VL_OUT8(&io_out_pdest,7,0);
    VL_OUT8(&io_out_int_wen,0,0);
    VL_OUT8(&io_out_fp_wen,0,0);
    VL_OUT8(&io_out_vec_wen,0,0);
    VL_OUT8(&io_out_v0_wen,0,0);
    VL_OUT8(&io_out_vl_wen,0,0);
    VL_OUT8(&io_out_fflags,4,0);
    VL_OUT8(&io_out_wflags,0,0);
    VL_OUT8(&io_out_vxsat,0,0);
    VL_OUT8(&io_fu_in_valid,2,0);
    VL_OUT8(&io_fu_in_ready,2,0);
    VL_OUT8(&io_fu_out_valid,2,0);
    VL_OUT8(&io_fu_out_ready,2,0);
    VL_OUT8(&io_fu_clock,2,0);
    VL_OUT8(&io_busy,0,0);
    VL_OUT8(&io_p_valid,0,0);
    VL_OUT8(&io_r_valid,0,0);
    VL_OUT8(&io_occupancy,1,0);
    VL_IN16(&io_op,8,0);
    VL_INW(&io_vs1,127,0,4);
    VL_INW(&io_vs2,127,0,4);
    VL_INW(&io_old_vd,127,0,4);
    VL_INW(&io_mask,127,0,4);
    VL_OUTW(&io_result,127,0,4);
    VL_OUTW(&io_result_vec,127,0,4);
    VL_OUTW(&io_result_v0,127,0,4);
    VL_OUT(&io_out_exception,23,0);
    VL_OUT(&io_out_ctrl,26,0);
    VL_OUTW(&io_in_vpu_full,194,0,7);
    VL_OUTW(&io_out_vpu_full,194,0,7);
    VL_OUTW(&io_in_perf_full,576,0,19);
    VL_OUTW(&io_out_perf_full,576,0,19);
    VL_IN64(&io_perf_tag,63,0);
    VL_OUT64(&io_out_perf_tag,63,0);
    VL_OUT64(&io_out_rename_tag,63,0);

    // CELLS
    // Public to allow access to /* verilator public */ items.
    // Otherwise the application code can consider these internals.
    VVDotElasticParentTestTop_SRT16Divint* const __PVT__VDotElasticParentTestTop__DOT__dut__DOT__Vidiv__DOT__vidiv__DOT___16bit_divide_0;
    VVDotElasticParentTestTop_SRT16Divint* const __PVT__VDotElasticParentTestTop__DOT__dut__DOT__Vidiv__DOT__vidiv__DOT___16bit_divide_1;
    VVDotElasticParentTestTop_SRT16Divint* const __PVT__VDotElasticParentTestTop__DOT__dut__DOT__Vidiv__DOT__vidiv__DOT___16bit_divide_2;
    VVDotElasticParentTestTop_SRT16Divint* const __PVT__VDotElasticParentTestTop__DOT__dut__DOT__Vidiv__DOT__vidiv__DOT___16bit_divide_3;

    // Root instance pointer to allow access to model internals,
    // including inlined /* verilator public_flat_* */ items.
    VVDotElasticParentTestTop___024root* const rootp;

    // CONSTRUCTORS
    /// Construct the model; called by application code
    /// If contextp is null, then the model will use the default global context
    /// If name is "", then makes a wrapper with a
    /// single model invisible with respect to DPI scope names.
    explicit VVDotElasticParentTestTop(VerilatedContext* contextp, const char* name = "TOP");
    explicit VVDotElasticParentTestTop(const char* name = "TOP");
    /// Destroy the model; called (often implicitly) by application code
    virtual ~VVDotElasticParentTestTop();
  private:
    VL_UNCOPYABLE(VVDotElasticParentTestTop);  ///< Copying not allowed

  public:
    // API METHODS
    /// Evaluate the model.  Application must call when inputs change.
    void eval() { eval_step(); }
    /// Evaluate when calling multiple units/models per time step.
    void eval_step();
    /// Evaluate at end of a timestep for tracing, when using eval_step().
    /// Application must call after all eval() and before time changes.
    void eval_end_step() {}
    /// Simulation complete, run final blocks.  Application must call on completion.
    void final();
    /// Are there scheduled events to handle?
    bool eventsPending();
    /// Returns time at next time slot. Aborts if !eventsPending()
    uint64_t nextTimeSlot();
    /// Trace signals in the model; called by application code
    void trace(VerilatedTraceBaseC* tfp, int levels, int options = 0) { contextp()->trace(tfp, levels, options); }
    /// Retrieve name of this model instance (as passed to constructor).
    const char* name() const;

    // Abstract methods from VerilatedModel
    const char* hierName() const override final;
    const char* modelName() const override final;
    unsigned threads() const override final;
    /// Prepare for cloning the model at the process level (e.g. fork in Linux)
    /// Release necessary resources. Called before cloning.
    void prepareClone() const;
    /// Re-init after cloning the model at the process level (e.g. fork in Linux)
    /// Re-allocate necessary resources. Called after cloning.
    void atClone() const;
  private:

    // Internal functions - the model's evaluation entry points
    void evalBegin() override final;
    void evalEnd() override final;
    void evalStatic() override final;
    void evalInitial() override final;
    bool evalStl(bool firstIteration) override final;
    void evalSample() override final;
    bool evalIco(bool firstIteration) override final;
    bool evalAct() override final;
    bool evalInact() override final;
    bool evalNba() override final;
    bool evalObs() override final;
    bool evalReact() override final;
    void evalPostponed() override final;
    void evalFinal() override final;
    void dumpTriggersStl() override final;
    void dumpTriggersIco() override final;
    void dumpTriggersAct() override final;
    void dumpTriggersNba() override final;
    void dumpTriggersObs() override final;
    void dumpTriggersReact() override final;

    // Internal functions - trace registration
    void traceBaseModel(VerilatedTraceBaseC* tfp, int levels, int options);
};

#endif  // guard
