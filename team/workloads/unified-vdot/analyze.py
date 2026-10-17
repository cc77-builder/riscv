"""Summarize only completed, calibrated full-core measurements."""
import argparse,csv,json,statistics
from pathlib import Path
import check

VARIANTS=('ours','jade','shishui','redoop')
LABELS={'ours':'本项目 T14','jade':'Jade','shishui':'试水','redoop':'Redoop（dot8适配）'}
SCENARIOS={'single':'单次点积','chain':'依赖链256','batch':'四路×32轮','stream':'加载/计算/存储64'}


def main(a):
    identity=json.loads((a.root/'audit/image-identity.json').read_text())
    check.require(identity['status']=='UNIFIED_INPUT_AND_BASELINE_IDENTITY_PASS','cross-image identity missing')
    records=[];all_samples=[]
    for variant in VARIANTS:
        path=a.root/'runs'/(variant+'-suite-02/result.json')
        check.require(path.exists(),'unfinished variant '+variant)
        result=json.loads(path.read_text())
        check.require(result['status']=='UNIFIED_FULLCORE_PASS','unaccepted variant '+variant)
        rows=[s for s in result['samples'] if s['stage']=='performance' and s['phase']=='measured']
        check.require(len(rows)==96,'expected 4 scenarios * 3 datasets * 4 measured pairs')
        all_samples.extend(rows)
        for scenario in SCENARIOS:
            selected=[s for s in rows if s['scenario']==scenario]
            methods={m:{(s['dataset'],s['repeat']):s for s in selected if s['method']==m} for m in ('vdot','rvv')}
            check.require(len(methods['vdot'])==12 and methods['vdot'].keys()==methods['rvv'].keys(),'unpaired samples')
            n={s['dots'] for s in selected};check.require(len(n)==1,'unequal work');dots=n.pop()
            custom=[s['cycles'] for s in methods['vdot'].values()];base=[s['cycles'] for s in methods['rvv'].values()]
            paired=[methods['rvv'][k]['cycles']/s['cycles'] for k,s in methods['vdot'].items()]
            records.append(dict(variant=variant,scenario=scenario,dots=dots,samples_per_method=12,
              custom_mean_cycles=statistics.mean(custom),custom_median_cycles=statistics.median(custom),
              custom_min_cycles=min(custom),custom_max_cycles=max(custom),custom_mean_cycles_per_dot=statistics.mean(custom)/dots,
              rvv_mean_cycles=statistics.mean(base),rvv_median_cycles=statistics.median(base),rvv_min_cycles=min(base),rvv_max_cycles=max(base),
              speedup_ratio_of_sums=sum(base)/sum(custom),paired_speedup_median=statistics.median(paired),paired_speedup_min=min(paired),paired_speedup_max=max(paired)))
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'result.json').write_text(json.dumps({'status':'UNIFIED_FOUR_PROJECT_COMPARISON_PASS','statistics':'three datasets, four measured rounds each; no overhead subtraction','rows':records,'samples':all_samples},indent=2)+'\n')
    with (a.output/'summary.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    with (a.output/'samples.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(all_samples[0]));writer.writeheader();writer.writerows(all_samples)
    lines=['# 四项目统一 vdot 周期比较','',
      '四个实现均通过本次统一全核 DiffTest、完整128位结果检查、计时边界与指令路径校验。以下为本机重新运行结果，未使用作者报告数字。','',
      '统一上游16ae / MinimalConfig / VLEN128 / 单核；三个输入数据集，每组四轮测量。窗口平均cycles包含循环和计时边界开销，不扣空循环。加速比=全部配对RVV cycles之和 ÷ 自定义cycles之和。','',
      '共64个全核测试镜像、860个已校验窗口，其中384个为正式性能测量窗口。每种实现、每个场景、每种方法各12个测量样本。10,022组大样本功能检查另在NEMU中完成，不混称为全核RTL验证。','',
      '源版本、适配细节与执行入口见归档目录的 `team/workloads/unified-vdot/README.md`；每个样本的cycles、指令计数和镜像信息见同目录 `samples.csv`。所有结果仅保存在本地，未推送GitHub。','']
    for scenario,label in SCENARIOS.items():
        lines += ['## '+label,'','| 实现 | 窗口平均cycles | cycles/dot | RVV平均cycles | 加速比 | 自定义范围 |','|---|---:|---:|---:|---:|---:|']
        for r in records:
            if r['scenario']!=scenario:continue
            lines.append(f"| {LABELS[r['variant']]} | {r['custom_mean_cycles']:.3f} | {r['custom_mean_cycles_per_dot']:.3f} | {r['rvv_mean_cycles']:.3f} | {r['speedup_ratio_of_sums']:.3f}× | {r['custom_min_cycles']}–{r['custom_max_cycles']} |")
        lines.append('')
    lines += ['## 解释范围','',
      '- Redoop原生为分lane dot4累加；本表包括使其完成相同dot8/full128接口的全部软件适配开销，不代表原生GEMM排名。',
      '- 单次窗口含固定开销，不等于FU延迟；四路的cycles/dot也不直接等于硬件II。',
      '- 四路场景对同一输入生成四个独立结果，不代表四组不同输入的实际应用。',
      '- 临时向量寄存器开销：三种原生dot8实现为0；Redoop单次1个/batch4为4个；RVV单次2个/batch4为8个。比较允许这些临时寄存器，不宣称全部寄存器逐指令等价。',
      '- 周期比较假设共同频率。未完成统一工艺和时序约束下的STA/PPA，不据此判断实际最高频率、功耗或芯片时间。',
      '- 本项目使用T14融合输入路径；T15独立INT16实验不改变该生产路径。',
      '- 本实验固定使用一套共同RVV算法，不代表穷尽软件优化后的最佳RVV性能。',
      '- 这是一次受控实验，不是官方跑分或获奖排名。','']
    (a.output/'统一测试结果.md').write_text('\n'.join(lines))
    print(json.dumps({'status':'UNIFIED_FOUR_PROJECT_COMPARISON_PASS','rows':len(records),'measured_samples':len(all_samples)}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);main(p.parse_args())
