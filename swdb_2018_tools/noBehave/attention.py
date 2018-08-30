import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from __future__ import print_function
drive_path = '/data/dynamic-brain-workshop/visual_behavior'
from visual_behavior.ophys.dataset.visual_behavior_ophys_dataset import VisualBehaviorOphysDataset
import visual_behavior.ophys.plotting.summary_figures as sf
from visual_behavior.ophys.response_analysis.response_analysis import ResponseAnalysis 
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis

def l0_event_pull(session):
    #input a session id, and output the array L0 events for each cell
    l0 = '/data/dynamic-brain-workshop/visual_behavior_events/%s_events.npz' % session
    l0_events = np.load(l0)['ev']
    return(l0_events)

def graph_compare(mouse1, mouse2, xlim1, xlim2, xlim3=None, xlim4=None): 
    #This function inputs two mice and xlimits, and will output 
    #two graphs with overlayed dff trace and L0 events, with stim events included
    if xlim3 == None:
        xlim3 = xlim1
        xlim4 = xlim2
    slc = mouse1
    vip = mouse2
    
    l0_events_vip = l0_event_pull(vip)
    l0_events_slc = l0_event_pull(slc)
    
    dataset_vip = VisualBehaviorOphysDataset(vip, cache_dir = drive_path)
    dataset_slc = VisualBehaviorOphysDataset(slc, cache_dir = drive_path)
    
    times_vip, traces_vip = dataset_vip.dff_traces
    times_slc, traces_slc = dataset_slc.dff_traces
    
    figsize = (10,10)
    fig, (ax1, ax2) = plt.subplots(2,1,figsize = figsize)

    ax1.plot(times_vip, traces_vip[1], label = 'dF/F Trace')
    ax1.plot(times_vip, l0_events_vip[1], label = 'L0 Events')


    for index in dataset_vip.stimulus_table.index:
        row_data = dataset_vip.stimulus_table.iloc[index]
        if ((row_data.start_time >= xlim1)&(row_data.end_time <= xlim2)):
            ax1.axvspan(xmin=row_data.start_time,xmax=row_data.end_time,facecolor='gray',alpha=0.3)

    ax2.plot(times_slc, traces_slc[4], label = 'dF/F Trace')
    ax2.plot(times_slc,l0_events_slc[4], label = 'L0 Events')

    for index in dataset.stimulus_table.index:
        row_data = dataset_slc.stimulus_table.iloc[index]
        if ((row_data.start_time >= xlim3)&(row_data.end_time <= xlim4)):
            ax2.axvspan(xmin=row_data.start_time,xmax=row_data.end_time,facecolor='gray',alpha=0.3)

    ax1.set_xlim(xlim1,xlim2)
    ax2.set_xlim(xlim3,xlim4)


    ax1.set_title('Vip dF/F vs L0 Events')
    ax2.set_title('Slc dF/F vs L0 Events')
    ax1.set_xlabel('Time(s)')
    ax1.set_ylabel('Event Size')
    
    ax1.legend()
    ax2.legend()
    
    ax2.set_xlabel('Time(s)')
    ax2.set_ylabel('Event Size')
    fig.tight_layout()
    ax.legend()

def experiments_for_donor_id (donor_id):
   # returns experiment_id in an array #
   holder_value = manifest[manifest.donor_id == donor_id]['experiment_id'].values
   return holder_value

def dataset_pull(session , drive_path = None):
    #this function simplifies the loading of a dataset by assuming the drive_path
    #input session_id and output dataset object
    from visual_behavior.ophys.dataset.visual_behavior_ophys_dataset import VisualBehaviorOphysDataset
    if drive_path == None:
        drive_path = '/data/dynamic-brain-workshop/visual_behavior'
    dataset = VisualBehaviorOphysDataset(session, cache_dir = drive_path)
    return(dataset)

def model_test(session, model, l0 = False, smooth = False, solver = None):
    #this function requires a binary model and a set of training data to output the LDA analysis
    #as an option you can use l0 events as training data, and you can choose to smooth the data
    
    #option for different analysis type is available
    
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    
    if l0 == False:
        training_data = dataset_pull(session)
    if l0 == True:
        training_data = l0_event_pull(session)
        
    if ((smooth == True)&(l0 == True)):
        return('This function is not yet supported')
    
    if ((smooth == True)&(l0 == False)):
        return('This function is not yet supported')
    
    time, trace = training_data.dff_traces
    if len(trace[0]) != len(model):
        return('Model does not match trace length for selected session')
    
    #ATTENTION
    #This step may need revision.  I believe the array needs to be reshaped in order to work but dont know why
    trace = np.swapaxes(trace, 0, 1)
    
    #This may also need revision, but its how I returned an output so I'm sticking with it
    
    if solver == None:
        solve = LinearDiscriminantAnalysis('svd')
    if solver == 'isqr':
        solve = LinearDiscriminantAnalysis('isqr')
    if solver == 'eigen':
        solve = LinearDiscriminantAnalysis('eigen')
    
    output = solve.fit_transform(trace, model)
    array = output[:,0]
    return(array)

''' This function is no longer being supported
def experiment_snip(experiment, start_list, end_list):
    #This is a sub-function that will be called within trace_snip
    #This function inputs one experiment, a start/end list and 
    #outputs an array of each cells trace in the experiment
    experiment = dataset_pull(experiment)
    time, trace = experiment.dff_traces
    trace_array = []
    
    for cell in trace:
        time_list =[]
        for i, start_time in enumerate(start_list):
            start_time = start_list[i]
            end_time = end_list[i]
            domain_indices = np.where(np.logical_and(time >=start_time, time < end_time))
            current_trace = cell[domain_indices]
            current_times = time[domain_indices]
            trace_list.extend(current_trace)
            time_list.extend(current_times)
        trace_array.append(trace_list)
    return(time_list, trace_array)
'''

def trace_snip(experiment,
               start_list,
               end_list,
               smooth = False,
               l0 = False,
               window_limit = 45,
               change_1 = 0.75,
               change_2 = 0.15,
               pre_change = False,
               pre_start_list = None,
               pre_end_list = None,
               all_pre_change = False,
               process = False, 
               per_cell = False, 
               one_cell = False):
    #Inputs dataframe, start times and stop times.  Outputs snips of neuron activity between the specified times
    #Experiment should be a VisualBehaviorOphysDataset object
    #Start should be a list of start times
    #End should be a list of end times
    frames = int((change_1 +change_2) * 30)
    trace_list = []
    time_list = []
    
    
    
    if len(start_list) != len(end_list):
        return('List of start and end times do not match')

    if ((l0 == True)&(smooth ==True)):
        return('I dont want to smooth an L0!')

    if l0 == True:
        exp_id = experiment.experiment_id
        l0 = '/data/dynamic-brain-workshop/visual_behavior_events/%s_events.npz' % exp_id
        trace = np.load(l0)['ev']
        time = experiment.timestamps_ophys

    else:
        time, trace = experiment.dff_traces

    for cell in trace:
        trace_list_temp = []
        if smooth == True:
            box = np.ones(10)/10
            cell = np.convolve(cell, box, 'same')
            
        if all_pre_change == False:    
            for j, start_time in enumerate(start_list):
                if pre_change == True:
                    pre_start_time = pre_start_list[j]
                    pre_end_time = pre_end_list[j]
                    domain_indices = np.where(np.logical_and(time >=pre_start_time, time < pre_end_time))
                    current_trace = cell[domain_indices]
                    current_times = time[domain_indices]
                    trace_list_temp.append(current_trace[:frames])
                    time_list.append(current_times)

                start_time = start_list[j]
                end_time = end_list[j]
                domain_indices = np.where(np.logical_and(time >=start_time, time < end_time))
                current_trace = cell[domain_indices]
                current_times = time[domain_indices]
                if process == True:
                    current_trace=current_trace.mean()
                    trace_list_temp.append(current_trace)
                else:
                    trace_list_temp.append(current_trace[:frames])
                time_list.append(current_times)
                
            if per_cell == True:
                trace_list.append(trace_list_temp)
            else:
                trace_list.extend(trace_list_temp)
            
        if all_pre_change == True:
            for j, pre_start_time in enumerate(pre_start_list):
                pre_start_time = pre_start_list[j]
                pre_end_time = pre_end_list[j]
                domain_indices = np.where(np.logical_and(time >=pre_start_time, time < pre_end_time))
                current_trace = cell[domain_indices]
                current_times = time[domain_indices]
                trace_list_temp.append(current_trace[:frames])
                time_list.append(current_times)
            trace_list.extend(trace_list_temp)
        if one_cell == True:
            break
        
    return(trace_list, time_list)

def engagement_a(experiment_list,
                 smooth = False,
                 l0 = False,
                 preview = False,
                 change_1 = 0.75,
                 change_2 = 0.15,
                 catch = False,
                 pre_change =False,
                 all_pre_change = False, 
                 process = False,
                 per_cell = False, 
                 model = False, 
                 wide_model = False, 
                 trials_before_and_after = 1, 
                 num_successes = 2,
                 time = False, 
                 meta = False, 
                 one_exp = False, 
                 one_cell = False):    
    
    #Experiment List: Requires experiment ids to be analyzed.  Must be a list
    #Smooth: If True, the program will return a smoothed trace instead of the raw dF/F
    #l0 : If True, the program will return the l0 Events instead of trace
    #preview: Used for printing a preview of the time window snips
    #change_1/change_2: Used to determine the window around the image change. change_1 is time in seconds before, change_2 is after
    #catch:  By default the program will return only Hits and Misses from 'go' trials.  If True, catch trials will be included
    #pre_change: If True, the program will pull both the change window, and the window of the last two image presentations
    #all_pre_change: If True, the program will only pull pre_change windows for the whole trial, except for the first 3 presentations
    #process: If True, the output of the trace/events will be the mean in that window rather than the full snip
    #per_cell: If True, returns the trace_array in a format that compares cells over trials.  Best used for one experiment
    #model: If True, will return the basic short window binary array corresponding to datapoints
    #wide_model: If True, will return the rolling "graded" binary window 
    #trials_before_and_after/num_success: If wide_model = True, these values are used to determine the grading for the engagement window. By default is 2/3
    #time: If True, will return the timepoints related to the snips
    #meta: If True, will return metadata such as presentation image type
    #one_exp: Use to reduce function run time and pull only information from the first experiment in the list
    #one_cell: same as one_exp, but only runs one cell
    
    
    
    
    #pass in a list of experiments and return an arrary of engagement binaries, and two arrays of start/end times
    
    
    #IN DEVELOPMENT
    #Optional argument for creating wide binary and wider binary
    

    eng_binary_array = []
    eng_trace_array = []
    eng_time_array = []
    for experiment in experiment_list:
        eng_start_array = []
        eng_end_array = []
        dataset = dataset_pull(experiment)
        trials = dataset.trials
        #create dataframe with engagement windows and simple engagement binary
        if pre_change == True:
            eng_st, eng_end, pre_eng_st, pre_eng_end = eng_window(trials,
                                                                  preview = preview,
                                                                  change_1 = change_1,
                                                                  change_2=change_2,
                                                                  catch= catch,
                                                                  pre_change= pre_change,
                                                                  all_pre_change = all_pre_change, 
                                                                  meta = meta)
        if meta == True:
            pre_eng_st = None
            pre_eng_end = None
            eng_st, eng_end, change_image_list = eng_window(trials,
                                         preview = preview,
                                         change_1 = change_1,
                                         change_2=change_2,
                                         catch= catch,
                                         pre_change= pre_change, 
                                         meta = meta)
            
            
        else:
            pre_eng_st = None
            pre_eng_end = None
            eng_st, eng_end = eng_window(trials,
                                         preview = preview,
                                         change_1 = change_1,
                                         change_2=change_2,
                                         catch= catch,
                                         pre_change= pre_change, 
                                         meta = meta)
            
        if model == True:
            eng_binary_temp = singletrial_eng_binary(trials,
                                                     preview = preview)
            
        if wide_model == True:
            eng_binary_temp = wide_engage_binary(trials, 
                                              preview = preview, 
                                              trials_before_and_after = trials_before_and_after, 
                                              num_successes = num_successes)
            
        trace_output, time_output_temp = trace_snip(dataset,
                                                    eng_st,
                                                    eng_end,
                                                    smooth=smooth,
                                                    l0=l0,
                                                    change_1=change_1,
                                                    change_2=change_2,
                                                    pre_change = pre_change,
                                                    pre_start_list = pre_eng_st,
                                                    pre_end_list = pre_eng_end,
                                                    all_pre_change = all_pre_change, 
                                                    process = process,
                                                    per_cell = per_cell, 
                                                    one_cell = one_cell)
        
        
        eng_trace_array.append(trace_output)
        eng_time_array.append(time_output_temp)
        
        if ((per_cell == False)&((model==True)|(wide_model==True))):
            for cells in range(len(dataset.cell_specimen_ids)):
                eng_binary_array.extend(eng_binary_temp)
        elif ((model == True)|(wide_model==True)):
            eng_binary_array.extend(eng_binary_temp)
        if one_exp == True:
            break
    if ((model == True)|(wide_model==True)):           
        eng_binary_array = np.array(eng_binary_array)
        
#INTERPRETING OF TRACE_OUTPUT
#The first level of the array is the index of the experiment in the list of experiments
#The second level of the array is the cell index from that experiment, and every trial
#The third level of the array is the trace

#IF PRE_CHANGE is TRUE
#The order of the trace list will be: evens are pre change, odds are post change

    trace_output = np.array(eng_trace_array)
    time_output = np.array(eng_time_array)
    if ((model == False)&(time==True)):
        return(trace_output, time_output)
    if (((model == True)|(wide_model == True))&(time==False)):
        return(trace_output, eng_binary_array)
    if ((model == False)&(time == False)&(meta == False)):
        return(trace_output)
    if meta == True:
        return(trace_output, change_image_list)
    return(eng_binary_array, trace_output, time_output)