import os
import numpy as np
import argparse
import pickle
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from library.comparison_class import variance_partitioning,multiple_regression
from library.rdm_loader import get_taskonomy_RDMs_all_blocks_lt,get_fMRI_RDMs_per_subject_lt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

def get_grouped_rdms(task_list_nogeometry,taskonomy_RDM_dir,layers):
    """To convert individual DNN RDMs to grouped DNN RDMs.

    Parameters
    ----------
    task_list_nogeometry : list
        List of tasks.
    taskonomy_RDM_dir : string
        path to Taskonomy DNN RDM directory
    layers : list
        List of layers to use.

    Returns
    -------
    lsit of list
        List of grouped RDMs into 2D,3D, and semantic.

    """
    tasks_2D =['autoencoder', 'colorization','denoise', 'edge2d',  \
                'inpainting_whole','keypoint2d', 'segment2d']
    tasks_3D = ['curvature', 'edge3d','reshade', 'rgb2depth', \
                'rgb2mist', 'rgb2sfnorm','segment25d','keypoint3d']
    tasks_semantic = ['class_1000', 'class_places','segmentsemantic']
    taskonomy_rdms = get_taskonomy_RDMs_all_blocks_lt(taskonomy_RDM_dir,layers,task_list_nogeometry)
    individual_rdms = []
    rdms_2d = np.zeros((len(layers),1225))
    rdms_3d = np.zeros((len(layers),1225))
    rdms_sem = np.zeros((len(layers),1225))
    individual_indices = []
    iterator = 0
    for key,value in taskonomy_rdms.items():
        print(key,len(value))
        individual_rdms.append(value)
        individual_indices.append(range(iterator,iterator+len(value)))
        iterator = iterator + len(value)
        if key in tasks_2D:
            rdms_2d = rdms_2d + np.array(value)
        elif key in tasks_3D:
            rdms_3d = rdms_3d + np.array(value)
        elif key in tasks_semantic:
            rdms_sem = rdms_sem + np.array(value)
    print(individual_indices)
    grouped_rdms = [list(rdms_2d/float(len(tasks_2D))),\
                    list(rdms_3d/float(len(tasks_3D))),\
                    list(rdms_sem/float(len(tasks_semantic)))]
    return grouped_rdms

def label_diff(ax,text,r1,r2,max_corr,yer1,yer2,ymax,barWidth):
    """Function to annotate significance between two bars.
    """
    dx = int(abs((r1-r2))+0.1)
    y = max(max_corr+ yer2/2, max_corr+ yer1/2) + 0.1*dx*ymax
    x = r1 + dx/2.0
    lx = r1+0.1*barWidth
    rx = r1+dx*barWidth-0.1*barWidth

    barh = 0.05*ymax*dx
    barx = [lx, lx, rx, rx]
    bary = [y, y+barh, y+barh, y]
    mid = ((lx+rx)/2, y+barh)

    ax.plot(barx, bary, c='black',linewidth=0.1)
    #props = {'connectionstyle':'bar','arrowstyle':'-',\
    #             'shrinkA':0.01/dx,'shrinkB':0.05/dx,'linewidth':1}
    ax.annotate(text, xy=(x,y+ 1.2*barh ), zorder=10)
    #ax.annotate('', xy=(r1+0.1*barWidth,y+ 0.02*ymax*dx), xytext=(r1+dx*barWidth-0.1*barWidth,y+ 0.02*ymax*dx), arrowprops=props)


def label_against_zero(ax,i,text,r,bars,yer,ymax):
    """Function to annotate significance of a bar against zero.
    """
    x = r - 0.04
    y = bars + yer/2 + 0.1*ymax
    ax.annotate(text, xy=(x,y), zorder=10)

def plot_allrois(rois,results,rsa_result_dir):
    """Short summary.

    Parameters
    ----------
    rois : list
        List of ROIs
    results : result object
        result of all rois.
    rsa_result_dir : string
        directory to save results

    Returns
    -------
    None

    """
    ventral_temporal = ['V1v','V2v','V3v','hV4','VO1','VO2','PHC1','PHC2']
    dorso_lateral = ['V1d','V2d','V3d','LO1','LO2','V3b','V3a',]
    parietal_frontal = ['IPS0','IPS1','IPS2','IPS3','IPS5','SPL1','FEF']
    good_rois = ventral_temporal + dorso_lateral

    fig,ax = plt.subplots( nrows=4, ncols=4 , sharex=True, sharey=True)
    count =0
    ymax = 0.32
    barWidth = 1
    models = ['2d','3d','semantic']
    color = [(0,0,1), (0,1,0), (1,0,1)]
    uvar_2D = []
    uvar_3D = []
    uvar_semantic = []
    num_rois = len(rois)
    num_tasks = 3
    for r,roi in enumerate(rois):
        if roi in good_rois or roi == rois[6] or roi == rois[16]:
            individual_variances_mean,error_bars,p_values,p_values_diff,total_variances_mean = results[roi]
            correlation = individual_variances_mean[:3].ravel()
            p_values = p_values.ravel()
            error_bar = error_bars.ravel()

            x=[]
            y=[]
            yers = []
            uvar_2D.append(correlation[0])
            uvar_3D.append(correlation[1])
            uvar_semantic.append(correlation[2])
            indices = range(len(correlation))
            for si in indices:
                w=models[si]
                x.append(w)
                y.append(correlation[si])
                yers.append(error_bar[si])
                #print (w, rbf_cka[w])

            row = int(count/4)
            col = int(count%4)
            barlist = ax[row,col].bar(range(len(correlation)), list(y),color = color,yerr = yers, align='center')
            # Plotting significant values *
            for i,si in enumerate(indices):
                if p_values[si]<0.05:
                    text = '*'
                    label_against_zero(ax[row,col],i,text,range(len(correlation))[i],y[i],yers[i],ymax)

            max_corr = max(y)
            for si1 in indices:
                for si2 in indices:
                    if si1>=si2:
                        continue
                    else:
                        if p_values_diff[si1,si2]<0.05:
                            text = '*'
                            #barplot_annotate_brackets(si1, si2, text, range(len(correlation)), list(y))

                            label_diff(ax[row,col],text,si1,si2,max_corr,yers[si1],yers[si2],ymax,barWidth)

            ax[row,col].spines["top"].set_visible(False)
            ax[row,col].spines["right"].set_visible(False)
            ax[row,col].spines["bottom"].set_position(("data",0))
            ax[row,col].set_xticks(range(len(correlation)), list(x))
            yticks = np.arange(0, 0.3, 0.1)
            ax[row,col].set_yticks(yticks)

            plt.setp(ax[row,col].get_xticklabels(), rotation=90)
            #plt.xlabel('Unique variance', axes=ax[row,col])
            #plt.ylabel('Task type', axes=ax[row,col])
            ax[row,col].set_ylim([0,ymax])
            #plt.legend(labels, ['2D', '3D','semantic','geometric'])
            ax[row,col].set_title(roi + ": $R^{2}=$" +  str( round(total_variances_mean['tv'][0],2)),x=0.38, y=0.85)#,loc = 'left')
            ax[row,col].tick_params(
            axis='x',          # changes apply to the x-axis
            which='both',      # both major and minor ticks are affected
            bottom=False,      # ticks along the bottom edge are off
            top=False,         # ticks along the top edge are off
            labelbottom=False) # labels along the bottom edge are off
            #ax.legend(handles=legend_elements, loc=(0.50,0.72))#'upper right')
            count+=1

    ax[3,3].spines["top"].set_visible(False)
    ax[3,3].spines["right"].set_visible(False)
    ax[3,3].spines["bottom"].set_visible(False)
    ax[3,3].spines["left"].set_visible(False)
    ax[3,3].tick_params(
            axis='x',          # changes apply to the x-axis
            which='both',      # both major and minor ticks are affected
            bottom=False,      # ticks along the bottom edge are off
            top=False,         # ticks along the top edge are off
            labelbottom=False)
    ax[3,3].tick_params(
            axis='y',          # changes apply to the x-axis
            which='both',      # both major and minor ticks are affected
            bottom=False,      # ticks along the bottom edge are off
            top=False,         # ticks along the top edge are off
            labelbottom=False)
    #ax[3,3].set_yticks([])
    fig.text(0.04, 0.5, 'Unique variance '+"$ (R^{2})$", va='center', rotation='vertical')

    plots_save_path = os.path.join(rsa_result_dir,"vpart.svg")
    plt.savefig(plots_save_path, bbox_inches="tight")
    print("Results saved in this directory: ", rsa_result_dir)
    plt.show()

def main():
    parser = argparse.ArgumentParser(description='ROI analysis with tasknomy grouped RDMs')
    parser.add_argument('--fMRI_RDMs_dir', help='fMRI_RDMs_dir',\
                        default = "./data/kastner_ROIs_RDMs_pearson", type=str)
    parser.add_argument('--DNN_RDM_dir', help='DNN_RDM_dir', \
                        default = "./data/RDM_taskonomy_bonner50", type=str)
    parser.add_argument('--roi_labels', help='roi label file path', \
                        default = "./data/ROIfiles_Labeling.txt", type=str)
    parser.add_argument('--results_dir', help='results_dir', \
                        default = "./results/grouped_DNNS_ROIs/", type=str)
    parser.add_argument('-np','--num_perm', help=' number of permutations to select for bootstrap',\
                        default = 10000, type=int)
    parser.add_argument('-stats','--stats', help=' t-test or permuting labels',\
                        default = 'permutation_labels', type=str)
    parser.add_argument('-bs_ratio','--bootstrap_ratio', help='ratio of conditions for bootstrap',\
                        default = 0.9, type=float)
    args = vars(parser.parse_args())

    # list of all tasks
    task_list_nogeometry = ['autoencoder','class_1000', 'class_places', 'colorization',\
                            'curvature', 'denoise', 'edge2d', 'edge3d', \
                            'inpainting_whole','keypoint2d', 'keypoint3d', \
                            'reshade', 'rgb2depth', 'rgb2mist', 'rgb2sfnorm', \
                            'segment25d', 'segment2d', 'segmentsemantic','random']

    # command line arguments
    layers = ['block4','encoder_output']
    fMRI_RDMs_dir = args['fMRI_RDMs_dir']
    taskonomy_RDM_dir = args['DNN_RDM_dir']
    stats_type = args['stats']
    num_perm = args['num_perm']
    bootstrap_ratio = args['bootstrap_ratio']

    # Loading ROI RDMs
    roi_label_file = args['roi_labels']
    roi_labels = pd.read_csv(roi_label_file)
    print(roi_labels)
    rois=roi_labels['roi']
    roi_ids=roi_labels['id']


    # result directory
    rsa_result_dir = os.path.join(args['results_dir'],'vpart','-'.join(layers))
    if not os.path.exists(rsa_result_dir):
        os.makedirs(rsa_result_dir)
    result_file_name = os.path.join(rsa_result_dir, stats_type +'.pkl')


    if not os.path.exists(result_file_name):
        # taskonomy grouped RDMs
        grouped_rdms = get_grouped_rdms(task_list_nogeometry,taskonomy_RDM_dir,layers)
        fmri_rdms = get_fMRI_RDMs_per_subject_lt(fMRI_RDMs_dir,rois)
        # Performing variance partitioning to find unique and shared variance explained by
        # grouped RDMs (2D, 3D, and semantic)
        results = {}
        for roi in rois:
            vpart = variance_partitioning(grouped_rdms,fmri_rdms[roi],'roi',stats_type)
            result = vpart.get_unique_variance(num_permutations=num_perm)
            results[roi] = result
            print("---------------------------------------------------------------------")
            print(roi)
            print(result)
        result_list = [rois,results]
        with open(result_file_name, 'wb') as f:  # Python 3: open(..., 'wb')
            pickle.dump(result_list, f)
    else:
        with open(result_file_name, 'rb') as f:  # Python 3: open(..., 'rb')
            rois,results = pickle.load(f)

    # plottting the unique variance explained by grouped RDMs
    plot_allrois(rois,results,rsa_result_dir)

if __name__ == "__main__":
    main()
