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

def experiment_snip(experiment, start_list, end_list):
    #This is a sub-function that will be called within trace_snip
    time, trace = experiment.dff_traces()
    
    for i, start_time in start_list:
        start_time = start_list[i]
        end_time = end_list[i]
        domain_indices = np.where(np.logical_and(time >=start_time, time < end_time))
        current_trace = trace[domain_indices]
        current_times = time[domain_indices]
        print(domain_indices)
        print(current_times)
        break
    return('ding')

def trace_snip(experiment_list, start_array, end_array, l0=False, smooth = False):
    #Inputs dataframe, start times and stop times.  Outputs snips of neuron activity between the specified times
    #Experiment should be a VisualBehaviorOphysDataset object
    #Start should be a list of start times
    #End should be a list of end times
    
    
    if start_array.shape != end_array.shape:
        return('List of start and end times do not match')
    
    if type(experiment_list[0]) == visual_behavior.ophys.dataset.visual_behavior_ophys_dataset.VisualBehaviorOphysDataset:
        if l0 = False:
            time, trace = experiment.dff_traces()
        elif l0 = True:
            l0 = '/data/dynamic-brain-workshop/visual_behavior_events/%s_events.npz' % exp_id
            l0_events = np.load(l0)['ev']
            time = experiment.timestamps_ophys

        for i, start_list in enumerate(start_array):
            end_list = end_array[i]
            for j, start_time in enumerate(start_list):
                start_snip = start_time
                end_snip = end_list[j]
                
    elif type(experiment_list[0]) == type(1):