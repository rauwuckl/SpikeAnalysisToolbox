import pandas as pd
import numpy as np
import csv


"""
Function to extract spikes from a binary or text file

Args:
    pathtofolder: String, Indicates path to output folder containing SpikeIDs/Times files
    binaryfile: Boolean Flag, Indicates if the output to expect is .bin or .txt (True/False)

Returns:
    pandas data frame with columns "ids" and "times" for the neuron id and spike time
"""
def pandas_load_spikes(pathtofolder, binaryfile, input_neurons=False):
    ids, times = get_spikes(pathtofolder=pathtofolder, binaryfile=binaryfile, input_neurons=input_neurons)
    return pd.DataFrame({"ids": ids, "times": times})


"""
Function to extract spike times and IDs from a binary or text file

Args:
    pathtofolder: String, Indicates path to output folder containing SpikeIDs/Times files
    binaryfile: Boolean Flag, Indicates if the output to expect is .bin or .txt (True/False)

Returns:
    ids: numpy array of neuron ids for each spike
    times: numpy array of spike times for each spike (corresponding to the ids
"""
def get_spikes(pathtofolder, binaryfile, input_neurons=False):
    spike_ids = list()
    spike_times = list()
    id_filename = 'Neurons_SpikeIDs_Untrained_Epoch0'
    times_filename = 'Neurons_SpikeTimes_Untrained_Epoch0'
    if (input_neurons):
        id_filename = 'Input_' + id_filename
        times_filename = 'Input_' + times_filename
    if (binaryfile):
        idfile = np.fromfile(pathtofolder +
                             id_filename + '.bin',
                             dtype=np.uint32)
        timesfile = np.fromfile(pathtofolder +
                                times_filename + '.bin',
                                dtype=np.float32)
        return idfile, timesfile
    else:
        # Getting the SpikeIDs and SpikeTimes
        idfile = open(pathtofolder +
                      id_filename + '.txt', 'r')
        timesfile = open(pathtofolder +
                         times_filename + '.txt', 'r')

        # Read IDs
        try:
            reader = csv.reader(idfile)
            for row in reader:
                spike_ids.append(int(row[0]))
        finally:
            idfile.close()
        # Read times
        try:
            reader = csv.reader(timesfile)
            for row in reader:
                spike_times.append(float(row[0]))
        finally:
            timesfile.close()
        return (np.array(spike_ids).astype(np.int),
                np.array(spike_times).astype(np.float))



"""
Imports the ids and times for all supfolders and stores them in a list of pandas data frames

Args:
    masterpath: The Masterpath (i.e. "/Users/dev/Documents/Gisi/01_Spiking_Simulation/01_Spiking Network/Build/output/") 
    subfolders: All of the Stimulations in and list that are supossed to be analysed (i.e.["ParameterTest_0_epochs_all/", "ParameterTest_0_epochs_8_Stimuli/"]).
                If only one is of interest use ["ParameterTest_0_epochs/"]
    extensions: All epochs that are supposed to be imported (i.e. ["initial/""] or ["initial", "testing/epoch1/", "testing/epoch2/", ..., "testing/epoch_n/"])
    input_layer: If you want to look at the input layer only set this to true. 

Returns:
    all_subfolders: all supfolder spikes. shape [subfolder][extension]-> pandas data frame with all the spikes
"""
def load_spikes_from_subfolders(masterpath, subfolders, extensions, input_layer):
    print("Start")
    all_subfolders = list()
    if input_layer:
        for subfol in subfolders:
            print(subfol)
            # print(subfolders[subfol])
            for ext in extensions:
                all_extensions = list()
                currentpath = masterpath + "/" + subfol + "/" + ext + "/"
                spikes = pandas_load_spikes(currentpath, True, True)
                all_extensions.append(spikes)

            all_subfolders.append(all_extensions)
    else:
        for subfol in subfolders:
            all_extensions = list()
            for ext in extensions:
                currentpath = masterpath + "/" + subfol + "/" + ext + "/"
                spikes = pandas_load_spikes(currentpath, True)
                all_extensions.append(spikes)

            all_subfolders.append(all_extensions)

    return all_subfolders


def load_testing_stimuli_info(experiment_folder):
    """
    load the information about the stimuli presented during testing. There is assumed to be a file "testing_list.txt" with the information in the experiment_folder
    :param experiment_folder: top level folder of the experiment
    :return:
    """
    objects = []
    current_object = {'count': 0, 'elements': set(), 'indices': list()}
    current_stim_index = 0
    with open(experiment_folder + "/testing_list.txt", "r") as file:
        for line in file:
            raw_text = line.strip()
            if raw_text == "*":
                # make new object
                objects.append(current_object)
                current_object = {'count': 0, 'elements': set(), 'indices': list()}
            else:
                current_object['elements'].add(raw_text)
                current_object['count'] += 1
                current_object['indices'] += [current_stim_index]
                current_stim_index += 1
    objects.append(current_object)

    proper_objects = [obj for obj in objects if obj['count'] != 0]
    return proper_objects


"""
Function to extract the pre, post, weight and delays of a network structure

Args:
    pathtofolder: string path to the folder in which network files are stored
    binaryfile: True/False flag if it is binary file
    intial_weighs: True/False flag wether to load initial weights

Returns:
    Pandas data frame with the following colums:
    pre: list of synapse presynaptic indices
    post: list of synapse postsynaptic indices
    delays: list of synaptic delays (in units of timesteps)
    init_weights: list of synaptic weights (before training) only if initial_weights=True
    weights: list of synaptic weights after training
"""
def load_network(pathtofolder, binaryfile, inital_weights):
    if pathtofolder[-1] != "/":
        pathtofolder += "/"

    pre, post, delays, init_weights , weights = _raw_load_network(pathtofolder, binaryfile, inital_weights)
    data = dict(pre=pre, post=post, delays=delays, weights=weights)
    if inital_weights:
        data['init_weights'] = init_weights

    return pd.DataFrame(data=data)


def _raw_load_network(pathtofolder, binaryfile, inital_weights):
    pre = list()
    post = list()
    delays = list()
    if inital_weights:
        init_weights = list()
    else:
        init_weights = None
    weights = list()

    if (binaryfile):
        pre = np.fromfile(pathtofolder +
                          'Synapses_NetworkPre' + '.bin',
                          dtype=np.int32)
        post = np.fromfile(pathtofolder +
                           'Synapses_NetworkPost' + '.bin',
                           dtype=np.int32)
        delays = np.fromfile(pathtofolder +
                             'Synapses_NetworkDelays' + '.bin',
                             dtype=np.int32)
        if inital_weights:
            init_weights = np.fromfile(pathtofolder + 'Synapses_NetworkWeights_Initial' + '.bin',
                                       dtype=np.float32)
        weights = np.fromfile(pathtofolder +
                              'Synapses_NetworkWeights' + '.bin',
                              dtype=np.float32)

        return pre, post, delays, init_weights, weights
    else:

        # For each file type output by the network, load them
        with open(pathtofolder + 'Synapses_NetworkPre.txt', 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=' ', quotechar='|')
            for row in reader:
                pre.append(int(row[0]))

        with open(pathtofolder + 'Synapses_NetworkPost.txt', 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=' ', quotechar='|')
            for row in reader:
                post.append(int(row[0]))

        with open(pathtofolder + 'Synapses_NetworkDelays.txt', 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=' ', quotechar='|')
            for row in reader:
                delays.append(int(row[0]))
        if inital_weights:
            with open(pathtofolder + 'Synapses_NetworkWeights_Initial.txt', 'r') as csvfile:
                reader = csv.reader(csvfile, delimiter=' ', quotechar='|')
                for row in reader:
                    init_weights.append(float(row[0]))

        with open(pathtofolder + 'Synapses_NetworkWeights.txt', 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=' ', quotechar='|')
            for row in reader:
                weights.append(float(row[0]))

    return (pre, post, delays, init_weights, weights)
