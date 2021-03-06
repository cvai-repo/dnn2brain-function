# -*- coding: utf-8 -*-
"""
Created on Mon Jun  8 13:08:40 2020

@author: kshitij
"""
import numpy as np
import torch
from library.ordinary_least_squares import OLS_pytorch
from tqdm import tqdm
from scipy.stats import spearmanr

def multiple_regression_rsa(ind_vars, dep_var):
    """Return R and R2.

    Parameters
    ----------
    ind_vars : list
        list of independent variables (usually model RDMs).
    dep_var : np.array
        dependent variable (model RDM).

    Returns
    -------
    tuple
        R and R2.

    """
    correlations = []
    for i,ind_var in (enumerate(ind_vars)):
        fast_sl_result = get_adjusted_rsquare(ind_var,dep_var)
        correlations.append(fast_sl_result)
    correlations = np.array(correlations)
    correlations[correlations<0] = 0
    correlations = np.sqrt(correlations)
    return correlations,correlations**2

def vpart2(ind_vars, dep_var):
    """Return unique and shared variance with 2 independent variables.

    Parameters
    ----------
    ind_vars : list
        list of independent variables (usually model RDMs).
    dep_var : np.array
        dependent variable (model RDM).

    Returns
    -------
    tuple
        unique variance and total variance.

    """
    ind_var = np.array(ind_vars[0]+ind_vars[1])
    R12 = get_adjusted_rsquare(ind_var,dep_var)

    R=[]
    for i in range(2):
        ind_var = np.array(ind_vars[i])
        R.append(get_adjusted_rsquare(ind_var,dep_var))
    y12 = R[1]+R[0]-R12
    y1 = R[0]-y12
    y2 = R[1]-y12
    individual_variances = np.array([y1,y2,y12])
    #individual_variances[individual_variances < 0] = 0
    ratios=100*individual_variances/R12
    total_variance =  R12
    return individual_variances, total_variance

def get_adjusted_rsquare(ind_var,dep_var):
    """Returns adjusted R2.

    Parameters
    ----------
    ind_vars : list
        list of independent variables (usually model RDMs).
    dep_var : np.array
        dependent variable (model RDM).

    Returns
    -------
        adjusted R2.

    """
    lm = OLS_pytorch()
    model = lm.fit(ind_var.T,dep_var)
    R= lm.score()
    #print(ind_var.shape)
    R = 1 - (1-R)*(ind_var.shape[1]-1)/(ind_var.shape[1]-ind_var.shape[0]-1)
    if (ind_var.shape[1]-ind_var.shape[0]-1)==0:
        print(("Denominator is " , ind_var.shape[1]-ind_var.shape[0]-1))
    return R

def vpart3(ind_vars, dep_var):
    """Return unique and shared variance with 3 independent variables.

    Parameters
    ----------
    ind_vars : list
        list of independent variables (usually model RDMs).
    dep_var : np.array
        dependent variable (model RDM).

    Returns
    -------
    tuple
        unique variance and total variance.

    """
    ind_var = np.array(ind_vars[0]+ind_vars[1]+ind_vars[2])
    #print("vpart3 ind var shape, dep var shape: ", ind_var.shape,dep_var.shape)
    R123 = get_adjusted_rsquare(ind_var,dep_var)

    ind_var = np.array(ind_vars[0]+ind_vars[1])
    R12 = get_adjusted_rsquare(ind_var,dep_var)

    ind_var = np.array(ind_vars[0]+ind_vars[2])
    R13 = get_adjusted_rsquare(ind_var,dep_var)

    ind_var = np.array(ind_vars[1]+ind_vars[2])
    R23 = get_adjusted_rsquare(ind_var,dep_var)

    R=[]
    for i in range(3):
        ind_var = np.array(ind_vars[i])
        R.append(get_adjusted_rsquare(ind_var,dep_var))
    #print(R)

    y123 = R[1]+R[2]+R[0]-R12-R13-R23+R123
    y12 = R[0]+R[1]-R12-y123
    y13 = R[0]+R[2]-R13-y123
    y23 = R[1]+R[2]-R23-y123
    y1 = R[0]-y12-y13-y123
    y2 = R[1]-y12-y23-y123
    y3 = R[2]-y13-y23-y123
    individual_variances = np.array([y1,y2,y3,y12,y13,y23,y123])
    #individual_variances[individual_variances < 0] = 0
    ratios=100*individual_variances/R123
    total_variance =  {}
    total_variance['tv'] =  R123
    total_variance['iv'] =  individual_variances
    return individual_variances[:3],total_variance

def vpart_general(ind_vars, dep_var):
    """Return unique and shared variance with n independent variables.

    Parameters
    ----------
    ind_vars : list
        list of independent variables (usually model RDMs).
    dep_var : np.array
        dependent variable (model RDM).

    Returns
    -------
    tuple
        unique variance and total variance.

    """
    all_ind_var = []
    for i in range(len(ind_vars)):
        all_ind_var = all_ind_var + ind_vars[i]
    all_ind_var_np = np.array(all_ind_var)
    #print("vpart3 ind var shape, dep var shape: ", ind_var.shape,dep_var.shape)
    Rall = get_adjusted_rsquare(all_ind_var_np,dep_var)

    y = []
    for index in range(len(ind_vars)):
        ind_var = all_ind_var[:index] + all_ind_var[index+1 :]
        ind_var_np = np.array(ind_var)
        R_wo_index = get_adjusted_rsquare(ind_var_np,dep_var)
        y.append(Rall-R_wo_index)

    individual_variances = np.array(y)
    #individual_variances[individual_variances < 0] = 0
    total_variance =  {}
    total_variance['tv'] =  Rall
    total_variance['iv'] =  individual_variances
    return individual_variances, total_variance
