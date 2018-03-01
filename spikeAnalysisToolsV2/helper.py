import numpy as np
import pandas as pd
"""
Converts a long spike train into separate stimuli based upon a duration

Args:
    spikes: pandas DataFrame with ids and times
    stimduration: float indicating the length of time by which to split the stimuli

Returns:
    spikes_per_stimulus: a list of pandas data frames with spikes and times
"""
def splitstimuli(spikes, stimduration):
    assert ("ids" in spikes)
    assert ("times" in spikes)
    num_stimuli = int(np.ceil(np.max(spikes.times) / stimduration))

    spikes_per_stimulus = list()

    for i in range(num_stimuli):
        mask = (spikes.times > (i * stimduration)) & (spikes.times < ((i + 1) * stimduration))
        spikes_in_stim = spikes[mask].copy()
        spikes_in_stim.times -= (i * stimduration)
        spikes_per_stimulus.append(spikes_in_stim)

    return spikes_per_stimulus


"""
Takes a nested list with firing rates and arranges them in two numpy tensors (exc, inh)

Args: 
    all_stimuli_rates: nested list of shape [stimulus][layer][exc/inh] -> pandas dataframe with fields "ids", "firing_rate"

Returns: 
    (excitatory, inhibitory) 
    each is a numpy array of shape [stimulus, layer, neuron_id] -> firing rate value

"""
def nested_list_of_stimuli_2_np(all_stimuli_rates):
    n_stimuli = len(all_stimuli_rates)
    n_layer = len(all_stimuli_rates[0])
    n_neurons_exc = len(all_stimuli_rates[0][0][0])
    n_neurons_inh = len(all_stimuli_rates[0][0][1])
    excitatory_rates = np.empty((n_stimuli, n_layer, n_neurons_exc))
    inhibitory_rates = np.empty((n_stimuli, n_layer, n_neurons_inh))

    for stimulus in range(n_stimuli):
        for layer in range(n_layer):
            excitatory_rates[stimulus, layer, :] = all_stimuli_rates[stimulus][layer][0].sort_values('ids').firing_rates # sorting should be unnecessary
            inhibitory_rates[stimulus, layer, :] = all_stimuli_rates[stimulus][layer][1].sort_values('ids').firing_rates

    return excitatory_rates, inhibitory_rates


def nested_list_of_epochs_2_np(all_epoch_rates):
    """
    Convert nested list to two numpy arrays
    :param all_epoch_rates: nestd list of shape [epoch][stimulus][layer][exc/inh] -> pandas dataframe with fields "ids" firing_rate
    :return: exc, inh - each a numpy array of shape [epoch, stimulus, layer, nueron_id] -> firing rate value
    """
    list_of_np_arrays = [nested_list_of_stimuli_2_np(epoch) for epoch in all_epoch_rates]
    exc, inh = zip(*list_of_np_arrays)
    # they are wrong now
    exc_np = np.concatenate([np.expand_dims(e, 0) for e in exc], axis=0)
    inh_np = np.concatenate([np.expand_dims(i, 0) for i in inh], axis=0)
    return exc_np, inh_np


def neuron_target_column_to_numpy_array(data, target_column, network_architecture):
    """pandas dataframe with a column about each neuron to 2 numpy array with the values in that shape

    Args:
        data: pandas dataframe with columns "ids" and target_column
        target_column: string of the name for the target column
        network_architecture: dict with usual fields
    Returns:
        (exc, inh)
        each a numpy array of shape [layer, neuron_id]
    """
    neurons_per_layer = network_architecture["num_exc_neurons_per_layer"] + network_architecture["num_inh_neurons_per_layer"]
    result_exc = np.zeros(([network_architecture["num_layers"], network_architecture["num_exc_neurons_per_layer"]]))
    result_inh = np.zeros(([network_architecture["num_layers"], network_architecture["num_inh_neurons_per_layer"]]))

    layerwise = split_into_layers(data, network_architecture)
    for i, layer_data in enumerate(layerwise):
        exc, inh = split_exc_inh(layer_data, network_architecture)
        result_exc[i, exc.ids.values] = exc[target_column].values
        result_inh[i, inh.ids.values] = inh[target_column].values

    return result_exc, result_inh

def take_multiple_elements_from_list(input_list, ids):
    """
    Take multiple elements indexed by ids out of input_list
    :param input_list: list of arbitrary elemtns
    :param ids: list of integers
    :return: [obj for obj, i in enumerate(input_list) if i in ids]
    """
    result = list()
    for i in ids:
        result.append(input_list[i])
    return result




def id_to_position(id, network_info, pos_as_2d=True):
    """
    given the id of a neuron it calculates its coordinates in the network
    :param id: global id of the neuron
    :param network_info: usual dict
    :param pos_as_2d: if True returned position is tuple [layer, row, column] if False tuple [layer, neuron_id]
    :return: is_it_excitatory? , tuple with position of neuron [layer, row, column] or [layer, neuron_id]
    """
    num_exc_neurons_per_layer = network_info["num_exc_neurons_per_layer"]
    num_inh_neurons_per_layer = network_info["num_inh_neurons_per_layer"]
    total_per_layer = num_exc_neurons_per_layer + num_inh_neurons_per_layer

    layer = id // total_per_layer
    id_within_layer = id - (layer * total_per_layer)

    exc_neuron = id_within_layer < num_exc_neurons_per_layer

    if exc_neuron:
        n_in_layer_type = num_exc_neurons_per_layer
    else:
        n_in_layer_type = num_inh_neurons_per_layer
        id_within_layer -= num_exc_neurons_per_layer

    if pos_as_2d:
        side_length = get_side_length(n_in_layer_type)

        x = id_within_layer // side_length
        y = id_within_layer % side_length

        return exc_neuron, (int(layer), int(y), int(x))
    else:
        return exc_neuron, (int(layer), int(id_within_layer))


def id_within_layer_to_pos(id, network_info, exc_neuron=True):
    """
    Calculate position of neuron with its layer
    :param id: tuple of shape (layer, neuron_id) or neuron_id (as int)
    :param network_info: usual dict
    :return: tupple of shape: (layer, row, column) or (row, column)
    """
    if len(id) == 2:
        neuron_id = id[1]
        layer = (id[0],)
    else:
        layer, neuron_id = tuple(), id

    num_exc_neurons_per_layer = network_info["num_exc_neurons_per_layer"]
    num_inh_neurons_per_layer = network_info["num_inh_neurons_per_layer"]

    if exc_neuron:
        n_in_layer_typ = num_exc_neurons_per_layer
    else:
        n_in_layer_typ = num_inh_neurons_per_layer

    side_length = get_side_length(n_in_layer_typ)

    x = neuron_id // side_length
    y = neuron_id % side_length

    result = (int(y), int(x))

    return layer + result





def position_to_id(pos, is_excitatory, network_info):
    """
    Calculate receptive field of a neuron
    :param pos: position of the neuron as a tuple [layer, line, column], or [layer, id_within_layer]
    :param is_excitatory: True -> excitatory neuron, False -> inhibitory neuron
    :param network_info: usual dict
    :return id: overall id of the neuron
    """
    if len(pos) == 3:
        layer, line, column = pos
        neuron_id = None # we cant calculate the neuron_id without knowing which layer type it is
    elif len(pos) == 2:
        layer, neuron_id = pos
    else:
        raise ValueError("pos does not have the right shape (tupple of length 2 or 3")

    num_exc_neurons_per_layer = network_info["num_exc_neurons_per_layer"]
    num_inh_neurons_per_layer = network_info["num_inh_neurons_per_layer"]
    total_per_layer = num_exc_neurons_per_layer + num_inh_neurons_per_layer

    first_in_layer_id = layer * total_per_layer

    if is_excitatory:
        n_in_layer_type = num_exc_neurons_per_layer
    else:
        n_in_layer_type = num_inh_neurons_per_layer
        first_in_layer_id += num_exc_neurons_per_layer

    side_length = np.sqrt(n_in_layer_type)

    if neuron_id is None:
        neuron_id = (column * side_length) + line

    if (side_length % 1 != 0):
        raise RuntimeError("The number of neurons ber layer is not a square number: {}".format(n_in_layer_type))

    id = first_in_layer_id + neuron_id

    return id

def get_side_length(n_in_layer_type):
    side_length = np.sqrt(n_in_layer_type)
    if (side_length % 1 != 0):
        raise RuntimeError("Tried to reshape something into square that wasn't actually a square number: {}".format(n_in_layer_type))
    return int(side_length)

def id_to_position_input(id, n_layer, side_length):
    """
    get input neuron coordinates
    :param id: id of the neuron
    :param n_layer: number of input layers
    :param side_length: length of the input layer grid
    :return: coordinates as (layer, y, x)
    """
    assert(id < 0)

    id = (-1 * id) - 1

    n_per_layer = side_length ** 2

    layer = id // n_per_layer

    assert(layer <  n_layer)

    id_within_layer = id - (n_per_layer * layer)

    x = id_within_layer // side_length
    y = id_within_layer % side_length

    return (layer, y, x)







"""
Splits layer into excitatory and inhibitory neurons

Args: 
    neuron_activity: pandas data frame with columnd "ids" the rest is arbitrary, only one layer
    network_architecture_info: dictionary with the fields: num_exc_neurons_per_layer, num_inh_neurons_per_layer

Returns:
    excitatory: containing only excitatory ones
    inhibitory: pandas data frame with same columns as neuron_activity containing only the inhibitory ones
"""
def split_exc_inh(neuron_activity, network_architecture_info):
    assert ('ids' in neuron_activity)
    num_exc_neurons_per_layer = network_architecture_info["num_exc_neurons_per_layer"]
    num_inh_neurons_per_layer = network_architecture_info["num_inh_neurons_per_layer"]
    total_per_layer = num_exc_neurons_per_layer + num_inh_neurons_per_layer

    excitatory = neuron_activity[neuron_activity.ids < num_exc_neurons_per_layer]
    inhibitory = neuron_activity[neuron_activity.ids >= num_exc_neurons_per_layer].copy()
    inhibitory.ids -= num_exc_neurons_per_layer

    return excitatory, inhibitory


"""
Divides the neuron activity into the different layers.
it is agnostic about which neuron information is saved in the table (e.g. spike timings or firing rates) 

Args:
    neuron_activity:  pandas data frame with a column "ids" 
    network_architecture_info: dictionary with the fields: num_exc_neurons_per_layer, num_inh_neurons_per_layer, num_layers
    
Returns:
    list of data frames each with columsn ids and whater it was before. (ids are reduced to start with 0 in each layer)
"""
def split_into_layers(neuron_activity, network_architecture_info):
    assert('ids' in neuron_activity)

    layerwise_activity = list()

    num_exc_neurons_per_layer = network_architecture_info["num_exc_neurons_per_layer"]
    num_inh_neurons_per_layer = network_architecture_info["num_inh_neurons_per_layer"]
    n_layers = network_architecture_info["num_layers"]
    total_per_layer = num_exc_neurons_per_layer + num_inh_neurons_per_layer

    for l in range(n_layers):
        mask = (neuron_activity.ids >= (l * total_per_layer)) & (neuron_activity.ids < ((l + 1) * total_per_layer))
        neurons_in_current_layer = neuron_activity[mask].copy()
        neurons_in_current_layer.loc[:, 'ids'] -= l * total_per_layer
        layerwise_activity.append(neurons_in_current_layer)

    return layerwise_activity



def _combine_spike_ids_and_times(ids, times):
    return pd.DataFrame({"ids": ids, "times": times})


def z_transform(data, axis=0):
    """
    z transform of the given data along the given axis
    :param data:
    :param axis: defaults to 0 which for data of shape [stimulus, layer, neuron_id] gives you the relative response for each stimulus
    :return:
    """
    mean = np.mean(data, axis=axis)
    sigma = np.std(data, axis=axis)

    transformed = (data - mean) / sigma

    return np.nan_to_num(transformed)



def reshape_into_2d(unshaped):
    """
    takes an arbitrary numpy array and replaces the last dimension with 2 dimensions of same length
    Args:
        unshaped: numpy array of shape [..., n_neurons]
    Returns:
        numpy array of shape [..., sqrt(n_neurons), sqrt(n_neurons]
    Raises:
        Exception if n_neurons is not a square
    """
    dimensions = unshaped.shape
    n_neurons = dimensions[-1]

    side_length = np.sqrt(n_neurons)
    if(side_length % 1 != 0):
        raise RuntimeError("The last dimension is not a square number: {}".format(n_neurons))

    side_length = int(side_length)


    return np.reshape(unshaped, dimensions[:-1] + (side_length, side_length), order="F")


def epoch_subfolders_to_tensor(all_epochs):
    """
    Converts a nested list of firing rates to 2 numpy arrays
    :param all_epochs: nested list of shape [epoch][stimulus][layer][excitatory/inhibitory] -> pandas dataframe with "ids" and "firing_rates"
    :return: exc_rates,
    """
    raise NotImplementedError("don't know what happend here")


def random_label(n_objects, n_transforms, n_repeats):
    """
    Create random label where each stimuli always is part of the same object througout multiple repeats
    :param n_objects: number of objects
    :param n_transforms: number of transforms per object
    :param n_repeats: how often is each stimulus presented. (assumed that all stimulus are presented before one is presented again)
    :return: array of indices belonging to an object
    """

    n_stimuli = n_objects * n_transforms

    one_presentation_of_all = np.random.choice(n_stimuli, size=(n_objects, n_transforms), replace=False)

    # repeat for multiple presentations
    all_presentations = [one_presentation_of_all + (r * n_stimuli) for r in range(n_repeats)]

    all_presentations_np = np.concatenate(all_presentations, axis=1)

    return [list(l) for l in all_presentations_np] # unpack the numpy into a list of lists

def object_list_2_boolean_label(object_list):
    """
    Transform object list to boolean label numpy array as used by the SingleCellDecoder class
    :param object_list: list of dictionaries. each is one object and contains the fields 'count' and 'indices'
    :return: numpy array of shape [n_objects, n_stimuli] -> True if the object is present in that stimulus
    """
    n_objects = len(object_list)
    n_stimuli = np.sum([o['count'] for o in object_list])

    label_for_classifier = np.zeros((n_objects, n_stimuli), dtype=bool)

    for i, o in enumerate(object_list):
        label_for_classifier[i, o['indices']] = True

    return label_for_classifier

def bool_label_matrix_to_mutually_exclusive_ids(bool_array):
    """
    Function to convert a boolean label matrix as the SingleCellDecoder uses to a list of stimulus ids (by object) as
    single cell information uses

    :param bool_array: numpy array of type boolean with shape [n_objects, n_stimuli]
    :return: list containing n_object lists. each of which contains the ids of the stimuli in that object
    :raise: ValueError if there is a stimulus that is part of multiple objects
    """

    assert(bool_array.dtype == bool)

    n_obj, n_stim = bool_array.shape

    # check that the objects are mutually exclusive
    n_obj_that_stimulus_is_part_of = np.count_nonzero(bool_array, axis=0)
    if np.any(n_obj_that_stimulus_is_part_of > 1):
        raise ValueError("A stimulus was part of multiple objects")

    # stimuli_that_are_part_of_object = (n_obj_that_stimulus_is_part_of == 1)

    print("{} stimuli are not part of an object".format(np.count_nonzero(n_obj_that_stimulus_is_part_of == 0)))

    collector = list()
    for o in range(n_obj):
        current_object = list(np.where(bool_array[o, :])[0])
        collector.append(current_object)

    return collector


def ids_to_bool_array(ids):
    """
    Converts a list of ids as needed for classic single cell information to a matrix of bools as needed for the single cell decoder
    :param ids: nested array of objects, each object is a list of corresponding ids [[2,3,4,5],[0,1,6,7]]
    :return: numpy array of shape (n_stims, n_objects)
    """
    n_stims = max_of_nested_array(ids) + 1
    n_objs  = len(ids)

    matrix = np.zeros((n_objs, n_stims), dtype=bool)

    for obj_id, obj in enumerate(ids):
        matrix[obj_id, obj] = True

    return matrix


def max_of_nested_array(arr):
    """rekursivly compute the maximum number in a arbitrary nested structure of arrays"""
    if type(arr) != list:
        return arr
    else:
        return max([max_of_nested_array(i) for i in arr])


def split_into_populations(neuron_values, network_architecture_info, population_name="L{layer}_{type}"):
    """
    Split pandas dataframe of neurons into neuron populations. A popluation is all neurons of one type (excitatory or inhibitory)
    within one layer.

    :param neuron_values: pandas dataframe with column "ids" and arbitrary additional columns
    :param network_architecture_info: dict with fields "num_exc_neurons_per_layer", "num_inh_neurons_per_layer", "num_layers"
    :return: dictionary with population_name as key (e.g. L0_exc) and pandas dataframe with same columns as neuron_values as value
    """
    result=dict()

    neuron_mask = NeuronMask(network_architecture_info)

    neuron_ids = neuron_values.ids.values

    for layer in range(network_architecture_info["num_layers"]):

        # excitatory
        name = population_name.format(layer=layer, type="exc")
        mask = neuron_mask.is_in_layer(neuron_ids, layer) & neuron_mask.is_excitatory(neuron_ids)
        values = neuron_values[mask]
        result[name] = values

        # inhibitory
        name = population_name.format(layer=layer, type="inh")
        mask = neuron_mask.is_in_layer(neuron_ids, layer) & neuron_mask.is_inhibitory(neuron_ids)
        values = neuron_values[mask]
        result[name] = values

    return result





class NeuronMask:
    def __init__(self, network_architecture_info):
        """
        Class that provides masks for a given network
        Each function returns a boolean array that is true where the neuron is of the correct type
        """

        self.n_exc = network_architecture_info["num_exc_neurons_per_layer"]
        self.n_inh = network_architecture_info["num_inh_neurons_per_layer"]
        self.total_per_layer = self.n_exc + self.n_inh
        self.n_layer = network_architecture_info["num_layers"]

        self.n_all_neurons = self.total_per_layer * self.n_layer

        self.last_exc = self.n_exc

    def _check_if_in_input_layer(self, neuron_ids):
        if np.any(neuron_ids < 0):
            raise NotImplementedError("Does not work for input neurons at the moment")

    def is_in_layer(self, neuron_ids, layer):
        """returns boolean array of shape neuron_ids which is true for each neuron_id that is in the layer"""
        self._check_if_in_input_layer(neuron_ids)

        return (neuron_ids // self.total_per_layer) == layer

    def _id_within_layer(self, neuron_ids):
        return neuron_ids % self.total_per_layer

    def is_excitatory(self, neuron_ids):
        self._check_if_in_input_layer(neuron_ids)
        ids_within_layer = self._id_within_layer(neuron_ids)
        return ids_within_layer < self.n_exc


    def is_inhibitory(self, neuron_ids):
        self._check_if_in_input_layer(neuron_ids)
        ids_within_layer = self._id_within_layer(neuron_ids)
        return ids_within_layer >= self.n_exc

    def get_ids_of_random_neurons_of_type(self, n_to_draw, restricting_functions = None):
        """
        Draw ids of random neurons that fullfill certain criteria
        :param n_to_draw: how many neurons to draw
        :param restricting_functions: list of functions that take a numpy array as input and return a boolean array of same shape as restrictions on the neurons. e.g. self.is_excitatory

        :return: numpy array of length n_to_draw
        """
        entire_pool = np.arange(0, self.n_all_neurons)

        neurons_left = entire_pool

        if restricting_functions:
            if type(restricting_functions) != list:
                restricting_functions = [restricting_functions]

            for fun in restricting_functions:
                neurons_left = neurons_left[fun(neurons_left)]

        return np.random.choice(neurons_left, n_to_draw, replace=False)

