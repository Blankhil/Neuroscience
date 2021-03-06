# %%
from collections import OrderedDict
from pylab import rcParams
import torch
import torch.nn as nn
import torchvision.transforms
import matplotlib.pyplot as plt
import numpy as np
import mne
from sklearn.preprocessing import RobustScaler
from ipywidgets import FloatProgress

import warnings
warnings.filterwarnings('ignore')

# %%
torch.manual_seed(100)

# Initialize parameters
eeg_sample_count = 240 # How many samples are we training
learning_rate = 1e-3 # How hard the network will correct its mistakes while learning
eeg_sample_length = 226 # Number of eeg data points per sample
number_of_classes = 1 # We want to answer the "is this a P300?" question
hidden1 = 500 # Number of neurons in our first hidden layer
hidden2 = 1000 # Number of neurons in our second hidden layer
hidden3 = 100 # Number of neurons in our third hidden layer
output = 10 # Number of neurons in our output layer

# %%
## Create sample data using the parameters
sample_positives = [None, None] # Element [0] is the sample, Element [1] is the class
sample_positives[0] = torch.rand(int(eeg_sample_count / 2), eeg_sample_length) * 0.50 + 0.25
sample_positives[1] = torch.ones([int(eeg_sample_count / 2), 1], dtype=torch.float32)

sample_negatives = [None, None] # Element [0] is the sample, Element [1] is the class
sample_negatives_low = torch.rand(int(eeg_sample_count / 4), eeg_sample_length) * 0.25
sample_negatives_high = torch.rand(int(eeg_sample_count / 4), eeg_sample_length) * 0.25 + 0.75
sample_negatives[0] = torch.cat([sample_negatives_low, sample_negatives_high], dim = 0)
sample_negatives[1] = torch.zeros([int(eeg_sample_count / 2), 1], dtype=torch.float32)

samples = [None, None] # Combine the two
samples[0] = torch.cat([sample_positives[0], sample_negatives[0]], dim = 0)
samples[1] = torch.cat([sample_positives[1], sample_negatives[1]], dim = 0)

## Create test data that isn't trained on
test_positives = torch.rand(10, eeg_sample_length) * 0.50 + 0.25 # Test 10 good samples
test_negatives_low = torch.rand(5, eeg_sample_length) * 0.25 # Test 5 bad low samples
test_negatives_high = torch.rand(5, eeg_sample_length) * 0.25 + 0.75 # Test 5 bad high samples
test_negatives = torch.cat([test_negatives_low, test_negatives_high], dim = 0)

print("We have created a sample dataset with " + str(samples[0].shape[0]) + " samples")
print("Half of those are positive samples with a score of 100%")
print("Half of those are negative samples with a score of 0%")
print("We have also created two sets of 10 test samples to check the validity of the network")

# %%
rcParams['figure.figsize'] = 15, 5 

plt.figure(1)
plt.title("Sample Data Set")
plt.plot(list(range(0, eeg_sample_length)), sample_positives[0][0], color = "#bbbbbb", label = "Samples")
plt.plot(list(range(0, eeg_sample_length)), sample_positives[0].mean(dim = 0), color = 'g', label = "Mean Positive")
plt.plot(list(range(0, eeg_sample_length)), sample_negatives_high[0], color = "#bbbbbb")
plt.plot(list(range(0, eeg_sample_length)), sample_negatives_high.mean(dim = 0), color = "r", label = "Mean Negative")
plt.plot(list(range(0, eeg_sample_length)), sample_negatives_low[0], color = "#bbbbbb")
plt.plot(list(range(0, eeg_sample_length)), sample_negatives_low.mean(dim = 0), color = "r")
plt.plot(list(range(0, eeg_sample_length)), [0.75] * eeg_sample_length, color = "k")
plt.plot(list(range(0, eeg_sample_length)), [0.25] * eeg_sample_length, color = "k")
plt.legend()
plt.show()

# %%
## Define the network
tutorial_model = nn.Sequential()

# Input Layer (Size 226 -> 500)
tutorial_model.add_module('Input Linear', nn.Linear(eeg_sample_length, hidden1))
tutorial_model.add_module('Input Activation', nn.CELU()) 

# Hidden Layer (Size 500 -> 1000)
tutorial_model.add_module('Hidden Linear', nn.Linear(hidden1, hidden2))
tutorial_model.add_module('Hidden Activation', nn.ReLU())

# Hidden Layer (Size 1000 -> 100)
tutorial_model.add_module('Hidden Linear2', nn.Linear(hidden2, hidden3))
tutorial_model.add_module('Hidden Activation2', nn.ReLU())

# Hidden Layer (Size 100 -> 10)
tutorial_model.add_module('Hidden Linear3', nn.Linear(hidden3, 10))
tutorial_model.add_module('Hidden Activation3', nn.ReLU())

# Output Layer (Size 10 -> 1)
tutorial_model.add_module('Output Linear', nn.Linear(10, number_of_classes))
tutorial_model.add_module('Output Activation', nn.Sigmoid())

# Define a loss function
loss_function = torch.nn.MSELoss()

# Define a training procedure
def train_network(train_data, actual_class, iterations):

  # Keep track of loss at every training iteration
  loss_data = []

  # Begin training for a certain amount of iterations
  for i in range(iterations):

    # Begin with a classification
    classification = tutorial_model(train_data)

    # Find out how wrong the network was
    loss = loss_function(classification, actual_class)
    loss_data.append(loss)

    # Zero out the optimizer gradients every iteration
    optimizer.zero_grad()

    # Teach the network how to do better next time
    loss.backward()
    optimizer.step()
  
  for index, item in enumerate(loss_data):
      print(item)
      loss_data[index] = item.detach().numpy()
      
  # Plot a nice loss graph at the end of training
  rcParams['figure.figsize'] = 10, 5
  plt.figure(2)
  plt.title("Loss vs Iterations")
  plt.plot(list(range(0, len(loss_data))), loss_data)

  plt.show()

# Save the network's default state so we can retrain from the default weigh
torch.save(tutorial_model, "/home/blanket/Neuroscience/EEG/p300_learner/tutorial_model_default_state")

# %%
# Step 5 Verify the Network Works

# Start from untrained 
tutorial_model = torch.load("/home/blanket/Neuroscience/EEG/p300_learner/tutorial_model_default_state")

# Define a learning function, need to be reinitialized every load
optimizer = torch.optim.Adam(tutorial_model.parameters(), lr = learning_rate)

# Train the network using our training procedure with the sample data
print("Below is the loss graph for our training session")
train_network(samples[0], samples[1], iterations = 100)
# %%

# Classify our positive test dataset
predicted_positives = tutorial_model(test_positives).data.tolist()

# Print the results 
for index, value in enumerate(predicted_positives):
    print("Positives test {1} Value scored: {0:.2f}%".format(value[0] * 100, index + 1))

print()

print("Below is a scatter plot of some of the samples")
print("Notice the distinct areas of red and green dots. If the input of this \n" +
"network was a simple x and y coordinate, the square band in the center would \n" +
"represent the \"solution space\" of our network. However, an actual EEG signal \n" +
"sample is an array of several points and can cross the boundry at any time.")
print("Plotted is one positive sample in green and two negative samples in red")

rcParams['figure.figsize'] = 10, 5
plt.scatter(list(range(0, eeg_sample_length)), test_positives[3], color = "#00aa00")
plt.plot(list(range(0, eeg_sample_length)), test_positives[3], color = "#bbbbbb")
plt.scatter(list(range(0, eeg_sample_length)), test_negatives[0], color = "#aa0000")
plt.plot(list(range(0, eeg_sample_length)), test_negatives[0], color = "#bbbbbb")
plt.scatter(list(range(0, eeg_sample_length)), test_negatives[9], color = "#aa0000")
plt.plot(list(range(0, eeg_sample_length)), test_negatives[9], color = "#bbbbbb")
plt.ylim([0 , 1])
plt.show()
# %%
data_path = mne.datasets.sample.data_path()
data_path
# %%
raw_fname = data_path + '/MEG/sample/sample_audvis_filt-0-40_raw.fif'
event_fname = data_path + '/MEG/sample/sample_audvis_filt-0-40_raw-eve.fif'

# Obtain a reference to the database and preload into RAM 
raw_data = mne.io.read_raw_fif(raw_fname, preload=True)

# EEGs work by detecting the voltage between two points. The second reference
# point is set to be the average of all voltages using the following function.
# It is also possible to set the reference voltage to a different number.
raw_data.set_eeg_reference()

# Define what data we want from the dataset
raw_data = raw_data.pick(picks=["eeg","eog"])
picks_eeg_only = mne.pick_types(raw_data.info, 
                                eeg=True, 
                                eog=True, 
                                meg=False, 
                                exclude='bads')

events = mne.read_events(event_fname)
event_id = 5
tmin = -0.5
tmax = 1
epochs = mne.Epochs(raw_data, events, event_id, tmin, tmax, proj=True,
                    picks=picks_eeg_only, baseline=(None, 0), preload=True,
                    reject=dict(eeg=100e-6, eog=150e-6), verbose=False)

print(epochs)

# This is the channel used to monitor the P300 response
channel = "EEG 058"

# Display a graph of the sensor position we're using
sensor_position_figure = epochs.plot_sensors(show_names=[channel])

event_id=[1,2,3,4]
epochsNoP300 = mne.Epochs(raw_data, events, event_id, tmin, tmax, proj=True,
                    picks=picks_eeg_only, baseline=(None, 0), preload=True,
                    reject=dict(eeg=100e-6, eog=150e-6), verbose = False)
print(epochsNoP300)

epochsNoP300[0:12].plot_image(picks=channel)

mne.viz.plot_compare_evokeds({'P300': epochs.average(picks=channel), 'Other': epochsNoP300[0:12].average(picks=channel)})

eeg_data_scaler = RobustScaler()

# We have 12 p300 samples 
p300s = np.squeeze(epochs.get_data(picks=channel))

# We have 208 non-p300 samples 
others = np.squeeze(epochsNoP300.get_data(picks=channel))

# Scale the p300 data using RobustScaler
p300s = p300s.transpose()
p300s = eeg_data_scaler.fit_transform(p300s)
p300s = p300s.transpose()

# Scale the non-p300 data using the RobustScaler
others = others.transpose()
others = eeg_data_scaler.fit_transform(others)
others = others.transpose()

## Prepare the train and test tensors
# Specify Positive P300 train and test samples
p300s_train = p300s[0:9]
p300s_test = p300s[9:12]
p300s_test = torch.tensor(p300s_test).float()

# Specify Negative p300 train and test samples
others_train = others[30:39]
others_test = others[39:42]
others_test = torch.tensor(others_test).float()

# Combine everything into their final structures
training_data = torch.tensor(np.concatenate((p300s_train, others_train), axis = 0)).float()
positive_testing_data = torch.tensor(p300s_test).float()
negative_testing_data = torch.tensor(others_test).float()

# Print the size of each of our data structures
print("training data count: " + str(training_data.shape[0]))
print("positive testing data count: " + str(positive_testing_data.shape[0]))
print("negative testing data count: " + str(negative_testing_data.shape[0]))

# Generate training labels 
labels = torch.tensor(np.zeros((training_data.shape[0],1))).float()
labels[0:10] = 1.0
print("training labels count: " + str(labels.shape[0]))

# Make sure we're starting from untrained every time
tutorial_model = torch.load("/home/blanket/Neuroscience/EEG/p300_learner/tutorial_model_default_state")

# Define a learning function, needs to be reinitialized every load
optimizer = torch.optim.Adam(tutorial_model.parameters(), lr = learning_rate)

# Use our training procedure with the sample data
print("Below is the loss graph for dataset training session")
train_network(training_data, labels, iterations = 50)

# Classify our positive test dataset and print the results
classification_1 = tutorial_model(positive_testing_data)
for index, value in enumerate(classification_1.data.tolist()):
  print("P300 Positive Classification {1}: {0:.2f}%".format(value[0] * 100, index + 1))

print()

# Classify our negative test dataset and print the results
classification_2 = tutorial_model(negative_testing_data)
for index, value in enumerate(classification_2.data.tolist()):
  print("P300 Negative Classification {1}: {0:.2f}%".format(value[0] * 100, index + 1))

rcParams['figure.figsize'] = 15, 5

plt.plot(list(range(0, eeg_sample_length)), positive_testing_data[0], color = "#00ff00")
plt.plot(list(range(0, eeg_sample_length)), positive_testing_data[1], color = "#00aa11")
plt.plot(list(range(0, eeg_sample_length)), positive_testing_data[2], color = "#448844")
plt.show()
plt.plot(list(range(0, eeg_sample_length)), negative_testing_data[0], color = "black")
plt.plot(list(range(0, eeg_sample_length)), negative_testing_data[1], color = "r")
plt.plot(list(range(0, eeg_sample_length)), negative_testing_data[2], color = "#994400")
plt.show()


import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
fig1 = plt.figure()
fig2 = plt.figure()
fig3 = plt.figure()
fig4 = plt.figure()
ax1 = fig1.add_subplot(111, projection='3d')
ax2 = fig2.add_subplot(111, projection='3d')
ax3 = fig3.add_subplot(111, projection='3d')
ax4 = fig4.add_subplot(111, projection='3d')

meta_parameters = dict(tutorial_model.named_parameters())
weight_data_input = meta_parameters['Input Linear.weight'].data.detach().numpy()
weight_data_hidden1 = meta_parameters['Hidden Linear.weight'].data.detach().numpy()
weight_data_hidden2 = meta_parameters['Hidden Linear2.weight'].data.detach().numpy()
weight_data_hidden3 = meta_parameters['Hidden Linear3.weight'].data.detach().numpy()
weight_data_output = meta_parameters['Output Linear.weight'].data.detach().numpy()

rcParams['figure.figsize'] = 10, 5

# Grab some test data.
X_1, Y_1 = np.meshgrid(range(1, 227), range(1, 501))
X_2, Y_2 = np.meshgrid(range(1, 501), range(1, 1001))
X_3, Y_3 = np.meshgrid(range(1, 1001), range(1, 101))
X_4, Y_4 = np.meshgrid(range(1, 101), range(1, 11))
X_5, Y_5 = np.meshgrid(range(1, 11), range(1, 1))

ax1.scatter(X_1, Y_1, weight_data_input, c = range(1, 113001), cmap = cm.plasma)
ax2.scatter(X_2, Y_2, weight_data_hidden1, c = range(1, 500001), cmap = cm.plasma)
ax3.scatter(X_3, Y_3, weight_data_hidden2, c = range(1, 100001), cmap = cm.plasma)
ax4.scatter(X_4, Y_4, weight_data_hidden3, c = range(1, 1001), cmap = cm.plasma)
plt.show()

# Let's take a look at the rest of the negative samples
others_train = others[30:39]
others_test = others[39:42]
rest_of_the_negative_samples = np.concatenate((others[0:30], others[42:208]), axis = 0)
rest_test = torch.tensor(rest_of_the_negative_samples)

# Combine to a torch tensor
rest_testing_data = torch.tensor(rest_test).float()

# Print the size Try
print("rest of the testing data count: " + str(rest_testing_data.shape[0]))

# Classify the rest of our data
classification = tutorial_model(rest_testing_data)
total_value = 0
number_correct = 0
for index, value in enumerate(classification.data.tolist()):
  print("P300 Negative Classification {1}: {0:.2f}%".format(value[0] * 100, index + 1))
  total_value += value[0] * 100
  if (value[0] < 0.5):
    number_correct += 1

print()
print("Average Negative Score: {0:.2f}%".format(total_value / 196))
print("Proportion of Non-P300s Classified Correctly: {0:.2f}%".format(float(number_correct) / 196.0 * 100.0))