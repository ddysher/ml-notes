# Install torch, torchvision and tensorboardX using pip (or conda), then run:
#  $ python tbx_log.py
#
# Once finished, run tensorboard:
#  $ tensorboard --logdir `pwd`/runs

import torch
import torchvision.utils as vutils
import numpy as np
import torchvision.models as models
from torchvision import datasets
from tensorboardX import SummaryWriter

resnet18 = models.resnet18(False)
sample_rate = 44100
freqs = [262, 294, 330, 349, 392, 440, 440, 440, 440, 440, 440]

# Create a new summary writer instance to log summary/events. Default path
# is current working directory + 'runs' + current_time + hostname.
writer = SummaryWriter()

for n_iter in range(100):
  #
  # Scalar values.
  dummy_s1 = torch.rand(1)
  dummy_s2 = torch.rand(1)

  # Data grouping by `slash`.
  writer.add_scalar('data/scalar1', dummy_s1[0], n_iter)
  writer.add_scalar('data/scalar2', dummy_s2[0], n_iter)
  writer.add_scalars(
    'data/scalar_group',
    {
      'xsinx': n_iter * np.sin(n_iter),
      'xcosx': n_iter * np.cos(n_iter),
      'arctanx': np.arctan(n_iter)
    },
    n_iter)

  dummy_img = torch.rand(32, 3, 64, 64)  # output from network
  if n_iter % 10 == 0:
    #
    # Image: actually similar to scalar, image is also defined as a sub-message
    # of the Summary proto definition.
    x = vutils.make_grid(dummy_img, normalize=True, scale_each=True)
    writer.add_image('Image', x, n_iter)

    #
    # Audio
    dummy_audio = torch.zeros(sample_rate * 2)
    for i in range(x.size(0)):
      # amplitude of sound should in [-1, 1]
      dummy_audio[i] = np.cos(freqs[n_iter // 10] * np.pi * float(i) / float(sample_rate))
    writer.add_audio('myAudio', dummy_audio, n_iter, sample_rate=sample_rate)

    #
    # Plain Text
    writer.add_text('Text', 'text logged at step:' + str(n_iter), n_iter)

    #
    # Histogram
    for name, param in resnet18.named_parameters():
      writer.add_histogram(name, param.clone().cpu().data.numpy(), n_iter)

    # needs tensorboard 0.4RC or later
    writer.add_pr_curve('xoxo', np.random.randint(2, size=100), np.random.rand(100), n_iter)

dataset = datasets.MNIST('mnist', train=False, download=True)
images = dataset.test_data[:100].float()
label = dataset.test_labels[:100]

features = images.view(100, 784)
writer.add_embedding(features, metadata=label, label_img=images.unsqueeze(1))

# Export scalar data to JSON for external processing: {writer_id : [[timestamp, step, value], ...], ...}
writer.export_scalars_to_json("./all_scalars.json")
writer.close()
