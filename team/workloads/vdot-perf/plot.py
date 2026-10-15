"""Plot every accepted paired observation once; repeated identical replays stay in source data."""
import argparse
import json
from pathlib import Path
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main(a):
    sys.path.insert(0,str(a.qa_scripts))
    from audit_panel_alignment import require_matplotlib_panel_alignment
    record=json.loads((a.analysis/'result.json').read_text())
    assert record['status']=='T13_FAIR_CYCLE_COMPARISON_PASS' and record['replay_identical']
    pairs=json.loads((a.analysis/'pairs.json').read_text())
    rows=[r for r in pairs if r['replay']==0]
    assert len(pairs)==702 and len(rows)==234
    order=[('single',1),('chain',16),('chain',64),('chain',256),('batch',1),('batch',8),('batch',32),('stream',1),('stream',16),('stream',64),('generic',1),('generic',16),('generic',64)]
    labels=[('Single' if s=='single' else 'Chain' if s=='chain' else 'Batch (4 dots/iter)' if s=='batch' else 'Load / dot / store' if s=='stream' else 'Preserve VL/vtype')+f'  |  n={n}' for s,n in order]
    plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],'font.size':8,'axes.titlesize':9,'axes.labelsize':8,'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':8,'svg.fonttype':'none','pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':0.7,'legend.frameon':False})
    fig,ax=plt.subplots(figsize=(7.2047244094,6.2992125984))  # 183 x 160 mm
    fig.subplots_adjust(left=0.34,right=0.97,bottom=0.13,top=0.9)
    settings=[('first','First pair','#8b9095','o',0.22),('warmup','Warm-up','#b77c32','x',0),('measured','Measured','#27658a','D',-0.22)]
    for phase,label,color,marker,offset in settings:
        xs,ys=[],[]
        for i,key in enumerate(order):
            group=[r for r in rows if (r['scenario'],r['n'])==key and r['phase']==phase]
            assert len(group)==(12 if phase=='measured' else 3)
            for j,r in enumerate(group):
                xs.append(r['speedup']);ys.append(i+offset+(j-(len(group)-1)/2)*0.009)
        ax.scatter(xs,ys,s=13 if phase=='measured' else 17,c=color,marker=marker,linewidths=0.7,label=label,zorder=3)
    ax.axvline(1,color='#555555',lw=0.8,ls='--',zorder=1)
    ax.set_yticks(range(len(order)),labels)
    ax.set_ylim(len(order)-0.5,-0.5)
    maximum=max(r['speedup'] for r in rows)
    assert maximum>0
    ax.set_xlim(0,maximum*1.08)
    ax.set_xlabel('Paired cycle ratio: RVV / vdot   (>1: vdot faster)')
    ax.set_title('Cycle benefit depends on workload and warm-up',loc='left',pad=31)
    ax.grid(axis='x',color='#e6e8ea',lw=0.5,zorder=0)
    ax.legend(loc='lower left',bbox_to_anchor=(0,1.005),ncol=3,borderaxespad=0,handletextpad=0.4,columnspacing=1)
    fig.text(0.34,0.04,'3 inputs; 4 measured pairs each. Fence and loop costs included.\nAll 3 fresh replays agree; only replay 0 is drawn.',fontsize=7,ha='left',va='bottom')
    a.output.mkdir(parents=True,exist_ok=False)
    stem=a.output/'paired-cycle-ratio'
    fig.canvas.draw()
    require_matplotlib_panel_alignment(fig,json_out=str(stem)+'.alignment.json',overlay_svg=str(stem)+'.alignment.svg',tolerance_pt=1.5,gutter_tolerance_pt=1.5,strict=True)
    fig.savefig(str(stem)+'.svg',facecolor='white')
    fig.savefig(str(stem)+'.pdf',facecolor='white')
    fig.savefig(str(stem)+'.png',dpi=600,facecolor='white')
    (a.output/'selection.json').write_text(json.dumps(dict(input_pairs=702,plotted_pairs=234,excluded_identical_replay_pairs=468,rule='replay == 0; all phases, sizes and datasets retained',statistics='raw paired ratios, no inference or confidence interval'),indent=2)+'\n')
    plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--analysis',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--qa-scripts',type=Path,required=True);main(p.parse_args())
