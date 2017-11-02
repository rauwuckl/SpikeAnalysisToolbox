import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from . import helper


def plot_activity_in_layers(excitatory, inhibitory, value_range=None, item_labels=None, cmap='plasma'):
    """
    Plot activity or information for all items in the network. items can be stimuli or objects for example
    :param excitatory: values for excitatory neurons to be plotted, shape [item, layer, neuron_id]
    :param inhibitory: same for inhibitory neurons
    :param value_range: value range of the color map (optional)
    :param item_labels: names for the item subplots (optional)
    :param cmap: colormap (optional)
    """
    n_presentation_items = excitatory.shape[0] #how many stimuli or objects
    num_layers = excitatory.shape[1]
    if not value_range:
        vmin = min(excitatory.min(), inhibitory.min())
        vmax = max(excitatory.max(), inhibitory.max())
    else:
        vmin, vmax = value_range



    if not item_labels:
        item_labels = range(n_presentation_items)
    else:
        assert(len(item_labels) == n_presentation_items)


    exc_rates_imgs = helper.reshape_into_2d(excitatory)
    inh_rates_imgs = helper.reshape_into_2d(inhibitory)

    n_above_exc = np.count_nonzero(excitatory > 0.9 * vmax, axis=2)
    n_above_inh = np.count_nonzero(inhibitory > 0.9 * vmax, axis=2)

    for item_id, item in enumerate(item_labels):
        fig = plt.figure(figsize=(19, 8))
        fig.suptitle("Item: {}".format(item), fontsize=16)

        for layer in range(num_layers):
            subPlotAX = fig.add_subplot(2, num_layers, layer + 1)



            subPlotAX.set_title("Excitatory - Layer {}, ({} info)".format(layer, n_above_exc[item_id, layer]))
            subPlotAX.imshow(exc_rates_imgs[item_id, layer, :, :], vmin=vmin, vmax=vmax, cmap=cmap)

            subPlotAXinh = fig.add_subplot(2, num_layers, num_layers + layer + 1)

            subPlotAXinh.set_title("Inhibitory - Layer {} ({} info)".format(layer, n_above_inh[item_id, layer]))
            im = subPlotAXinh.imshow(inh_rates_imgs[item_id, layer, :, :], vmin=vmin, vmax=vmax, cmap=cmap)

        cax = fig.add_axes([0.9, 0.1, 0.03, 0.8])
        fig.colorbar(im, cax=cax)


def animate_neuron_value_development(exc, inh):
    """
    Animate the development of a value per neuron
    :param exc: numpy array of shape [timepoint, layer, neuronid]
    :param inh: same
    :return: Animation
    """
    n_timepoints, n_layers, _n_neurons = exc.shape

    max_firing_rate = max(np.max(exc), np.max(inh))

    exc_img = helper.reshape_into_2d(exc)
    inh_img = helper.reshape_into_2d(inh)

    fig = plt.figure(figsize=(19, 8))

    exc_axes = []
    inh_axes = []
    for l in range(n_layers):
        exc_axes.append(fig.add_subplot(2, n_layers, 1 + l))
        exc_axes[-1].axis('off')
    for l in range(n_layers):
        inh_axes.append(fig.add_subplot(2, n_layers, n_layers + 1 + l))
        inh_axes[-1].axis('off')

    ims = []
    for frame in range(n_timepoints):
        # image_arr = np.reshape(exc[3, frame, :], (64, 64), order='F')
        images_Ex = []
        images_In = []
        for l in range(n_layers):
            imEx = exc_axes[l].imshow(exc_img[frame, l, :, :], animated=True, cmap='hot', vmin=0, vmax=max_firing_rate)
            imIn = inh_axes[l].imshow(inh_img[frame, l, :, :], animated=True, cmap='hot', vmin=0, vmax=max_firing_rate)

            images_Ex.append(imEx)
            images_In.append(imIn)

        ims.append(images_Ex + images_In)

    cax = fig.add_axes([0.92, 0.17, 0.03, 0.67])
    fig.colorbar(imIn, cax=cax)

    ani = animation.ArtistAnimation(fig, ims, interval=200, blit=True, repeat_delay=22000)
    return ani

def plot_values_all_layer(values, figure_title, cmap='plasma'):
    """
    Plot the values for all layers collor coded
    :param values: np array of shape [layer, neuron_id] or [layer, lines, columns]
    :param figure_title: title of the figure
    :param cmap: colormap to be used
    :return:
    """
    num_layers = values.shape[0]
    vmin =values.min()
    vmax =values.max()

    fig = plt.figure(figsize=(19, 8),)
    fig.suptitle(figure_title, fontsize=16)

    if(len(values.shape) > 1 and values.shape[-2] != values.shape[-1]):
        reshaped = helper.reshape_into_2d(values)
    else:
        reshaped = values

    for layer in range(num_layers):
        subPlotAX = fig.add_subplot(2, np.ceil(num_layers/2), layer + 1)

        subPlotAX.set_title("Values for Layer {}".format(layer))
        im = subPlotAX.imshow(reshaped[layer, :, :], vmin=vmin, vmax=vmax, cmap=cmap)

    cax = fig.add_axes([0.95, 0.2, 0.03, 0.6])
    fig.colorbar(im, cax=cax)






def plot_information_measure_advancement(before, after, n_to_plot = 1000, item_label=None):
    assert(before.shape == after.shape)
    n_objects, n_layer, n_neurons = before.shape

    if not item_label:
        item_label = list(range(n_objects))
    else:
        assert(len(item_label) == n_objects)

    before = np.sort(before, axis=2)
    after = np.sort(after, axis=2)

    vmax = max(np.max(before), np.max(after))


    fig = plt.figure(figsize=(18, 10))
    fig.suptitle("Information Measure before and after", fontsize=16)


    for layer in range(n_layer):
        for i, item in enumerate(item_label):

            layerAX  = fig.add_subplot(n_layer, n_objects, (n_objects * layer) + i + 1)
            layerAX.set_title("Info Item: {}, Layer {}".format(item, layer))

            layerAX.plot(before[i, layer, :-n_to_plot:-1], label="before")
            layerAX.plot( after[i, layer, :-n_to_plot:-1], label="after")

            layerAX.set_ylim(-0.1 * vmax, 1.1 * vmax)
            layerAX.legend()



def plot_information_difference_development(info, threshold):
    """
    plot how the difference in information between 2 stimuli developed
    :param info: np array of shape [epochs, objects, layer, neuron_id]
    :return:
    """
    n_epochs, n_objects, n_layer, n_neurons = info.shape

    if(n_objects !=2):
        raise NotImplementedError("At the moment, it only knows how to compare 2 objects.")

    avg_info = np.mean(info, axis=3)

    avg_info_1_minus_0 = avg_info[:, 1, :] - avg_info[:, 0, :]

    avg_max = np.max(avg_info)

    n_above_threshold = np.count_nonzero( (info >= threshold), axis=3 )
    max_n_above_threshold = np.max(n_above_threshold)

    above_max_1_minus_0 = n_above_threshold[:, 1, :] - n_above_threshold[:, 0, :]

    fig = plt.figure(figsize=(18, 8))
    fig.suptitle("Development of the difference in information", fontsize=16)


    axAvg  = fig.add_subplot(1, 2, 1)
    axAvg.set_ylim(0, 1.1 * avg_max)
    axAvg.set_title("Average info for stimulus 1 - avg info for stimulus 0")


    axN_neurons = fig.add_subplot(1, 2, 2)
    axN_neurons.set_ylim(0, 1.1 * max_n_above_threshold)
    axN_neurons.set_title("Number of neurons above {}".format(threshold))

    for l in range(n_layer):

        axAvg.plot(avg_info_1_minus_0[:, l], label= "Layer {}".format(l))
        axN_neurons.plot(above_max_1_minus_0[:, l], label="Layer {}".format(l))

    axAvg.legend()
    axN_neurons.legend()

def plot_information_development(info, threshold, item_label=None):
    """
    plot how the information developed
    :param info: np array of shape [epochs, objects, layer, neuron_id]
    :return:
    """
    n_epochs, n_objects, n_layer, n_neurons = info.shape
    if not item_label:
        item_label = list(range(n_objects))
    else:
        assert(len(item_label) == n_objects)

    avg_info = np.mean(info, axis=3)
    avg_max = np.max(avg_info)

    n_above_threshold = np.count_nonzero( (info >= threshold), axis=3 )
    n_above_max = np.max(n_above_threshold)

    fig = plt.figure(figsize=(18, 15))
    fig.suptitle("Development of the information", fontsize=16)

    for i, item in enumerate(item_label):

        axAvg  = fig.add_subplot(2, n_objects, i + 1)
        axAvg.set_ylim(0, 1.1 * avg_max)
        axAvg.set_title("Average info for Item {}".format(item))


        axN_neurons = fig.add_subplot(2, n_objects, n_objects + i + 1)
        axN_neurons.set_ylim(0, 1.1 * n_above_max)
        axN_neurons.set_title("Number of neurons above {}".format(threshold))

        for l in range(n_layer):

            axAvg.plot(avg_info[:, i, l], label= "Layer {}".format(l))
            axN_neurons.plot(n_above_threshold[:, i, l], label="Layer {}".format(l))

        axAvg.legend()
        axN_neurons.legend()


def plot_firing_rates_colored_by_object(firing_rates, object_list, title_string):
    if len(firing_rates.shape) != 1:
        raise ValueError("firing_rates has to be a single 'timecourse' of firing rates. only one neuron (or the mean) at a time")


    fig = plt.figure(figsize=(10, 7))
    fig.suptitle(title_string)
    ax = fig.add_subplot(1,1,1)
    ax.set_title("Firing Rates for Stimulus presentations, colored by object which contains the indicated stimuli")

    for obj in object_list:
        ids_in_obj = obj['indices']

        ax.plot(ids_in_obj, firing_rates[ids_in_obj], 'x', label=obj['elements'])

    ax.legend()

def plot_firing_rates_std_vs_mean_colored_by_object(firing_rates, object_list, title_string):
    """
    within a set of neurons (usually a layer) the mean fr and the std of it is computed and plotted

    :param firing_rates: np array of shape (objects, neuron_ids)
    :param object_list:
    :param title_string:
    :return:
    """
    if len(firing_rates.shape) != 2:
        raise ValueError("firing_rates has to be a single 'timecourse' of firing rates. only one neuron (or the mean) at a time")


    fr_mean = np.mean(firing_rates, axis=1)
    fr_std = np.std(firing_rates, axis=1)

    fig = plt.figure(figsize=(10, 7))
    fig.suptitle(title_string)
    ax = fig.add_subplot(1,1,1)
    ax.set_title("Firing Rate mean vs std for Stimulus presentations, colored by object which contains the indicated stimuli")

    for obj in object_list:
        ids_in_obj = obj['indices']

        ax.plot(fr_std[ids_in_obj], fr_mean[ids_in_obj], 'x', label=obj['elements'])

    ax.set_ylabel("Mean Firing Rate")
    ax.set_xlabel("Standard diviation of Firing Rate")
    ax.legend()


def plot_animated_histogram(data, n_bins=10, item_label=None, log=True):
    """
    Plot animated histograms of the data, one frame for each epoch

    :param data: numpy array of shape [epochs, objects, layer, neuron_id]
    :param item_label: lables of the items.
    :return:
    """
    n_epochs, n_objects, n_layer, n_neurons = data.shape
    if not item_label:
        item_label = list(range(n_objects))
    else:
        assert(len(item_label) == n_objects)

    vmin = np.min(data)
    vmax = np.max(data)

    bins = np.linspace(vmin, vmax, n_bins +1)

    fig = plt.figure(figsize=(19, 8))

    object_axes = []
    for obj in range(n_objects):
        layer_in_obj_axes = []
        for l in range(n_layer):
            layer_and_obj_axis = fig.add_subplot(n_layer, n_objects, l * n_objects + obj + 1)
            layer_and_obj_axis.hist(data[0, obj, l, :], bins=bins, log=log)
            # layer_and_obj_axis.yscale('log', nonposy='clip')
            layer_in_obj_axes.append(layer_and_obj_axis)
        object_axes.append(layer_in_obj_axes)

    def update_hist(num):
        for obj in range(n_objects):
            for l in range(n_layer):
                object_axes[obj][l].cla()
                object_axes[obj][l].hist(data[num, obj, l, :], bins=bins, log=log)

    ani = animation.FuncAnimation(fig, update_hist, n_epochs)
    return ani


def plot_connection_fields(synapses, layer, is_excitatory, neuron_positions, network_architecture, mode='sources'):
    """

    :param synapses:
    :param layer:
    :param is_excitatory:
    :param neuron_positions:
    :param network_architecture:
    :param mode: 'sources' or 'targets' plot the source neurons that map onto the ones given by neuron_position or plot the target neurons that the neuron_positions neuron map onto
    :return:
    """

    from . import synapse_analysis
    n_plots = len(neuron_positions)

    if is_excitatory:
        input_neuron_layer_side_length = helper.get_side_length(network_architecture["num_exc_neurons_per_layer"])
        # sidelength of the layer in which the neuron lives, who's position we inputed
    else:
        input_neuron_layer_side_length = helper.get_side_length(network_architecture["num_inh_neurons_per_layer"])


    fig = plt.figure("Receptive field for the following neurons in layer {}".format(layer), figsize=(19,8))
    for i,pos in enumerate(neuron_positions):

        ax = fig.add_subplot(2, np.ceil(n_plots/2), i+1)

        if(mode=='sources'):
            recpField = synapse_analysis.receptive_field_of_neuron((layer,) + pos, is_excitatory, synapses, network_architecture)
        elif(mode=='targets'):
            recpField = synapse_analysis.targets_of_neuron((layer,) + pos, is_excitatory, synapses, network_architecture)
        else:
            raise ValueError("mode can only be sources, or targets")


        ax.set_title("Neuron at {}, n_synapses: {}".format(pos, np.sum(recpField)))

        plotting_layer_side_length = recpField.shape[0]
        # sidelength of layer in which the receptive field lives

        factor = plotting_layer_side_length / input_neuron_layer_side_length
        # if for example we are looking at E2I Lateral synapses, then there are different number of neurons in the presynamptic and the postsynaptic layer
        # this factor mitigates that. the center of the receptive field of inhibitory neuron 16,16 is placed over the excitatory neuron 32, 32
        # because there are 32x32 inhibitory neurons and 64x64 excitatory ones

        im = ax.imshow(recpField, cmap='plasma')
        ax.scatter([pos[1]*factor], [pos[0]*factor], color="green", marker='x', s=500)
        fig.colorbar(im)
        ax.invert_xaxis()
        ax.invert_yaxis()
        ax.set_ylim(0, recpField.shape[0])
        ax.set_xlim(0, recpField.shape[1])

