import numpy as np
import matplotlib.pyplot as plt
import torch
from torch.nn import MSELoss
from torch.utils.data import DataLoader, TensorDataset
from tqdm import tqdm

from models import Autoencoder, MTL, logger, load_session
import utils


""" settings """

info, autoencoder = load_session(idx=0)

dim_ei = info["dim_ei"]
dim_ca3 = info["dim_ca3"]
dim_ca1 = info["dim_ca1"]
dim_eo = info["dim_eo"]

K_lat = info["K_lat"]
beta = info["beta"]
K = info["K"]

# get weights from the autoencoder
W_ei_ca1, W_ca1_eo = autoencoder.get_weights()

logger("<<< Loaded session >>>")


""" data """

num_samples = 400
num_rep = 4
datasets = []

stimuli = utils.sparse_stimulus_generator(N=num_samples,
                                          K=K,
                                          size=dim_ei,
                                          plot=False)

datasets = []
for k in range(num_samples):
    data = torch.tensor(stimuli[:k+1], dtype=torch.float32)
    dataloader = DataLoader(TensorDataset(data),
                            batch_size=1,
                            shuffle=False)
    datasets += [dataloader]

"""

[[s1]
 [s1, s2]
 ...]

"""


""" run """

outputs = np.zeros((num_rep, num_samples, num_samples)) - 1
for l in tqdm(range(num_rep)):

    # data
    stimuli = utils.sparse_stimulus_generator(N=num_samples,
                                              K=K,
                                              size=dim_ei,
                                              plot=False)

    datasets = []
    for k in range(num_samples):
        data = torch.tensor(stimuli[:k+1], dtype=torch.float32)
        dataloader = DataLoader(TensorDataset(data),
                                batch_size=1,
                                shuffle=False)
        datasets += [dataloader]

    # run
    for i in tqdm(range(num_samples)):

        # make model
        model = MTL(W_ei_ca1=W_ei_ca1,
                    W_ca1_eo=W_ca1_eo,
                    dim_ca3=dim_ca3,
                    lr=1.,
                    K_lat=K_lat,
                    K_out=K,
                    beta=beta)

        # train
        model.eval()
        with torch.no_grad():
            for batch in datasets[i]:
                # forward
                _ = model(batch[0].reshape(-1, 1))

        # test
        model.pause_lr()
        model.eval()
        with torch.no_grad():
            for j, batch in enumerate(datasets[i]):
                x = batch[0].reshape(-1, 1)

                # forward
                y = model(x)
                # logger.debug(f"{x.shape}, {y.shape}")

                # record : cosine similarity
                outputs[l, i, j] = (y.T @ x) / \
                    (torch.norm(x) * torch.norm(y))


""" plot """

plt.figure()

plt.subplot(121)
outputs = outputs.mean(axis=0)
plt.imshow(outputs, cmap="viridis",
           vmin=0, vmax=1, aspect="equal",
           interpolation="nearest")

plt.colorbar()
plt.xlabel("stimuli in a run")
# plt.xticks(range(num_samples), range(1, num_samples+1))
plt.ylabel("different runs")
# plt.yticks(range(num_samples), range(1, num_samples+1))

plt.title(f"MSE loss | {K_lat=} {beta=} {K=}")


plt.subplot(122)

vdiag = np.diag(outputs).flatten()

plt.plot(vdiag, 'k-')
plt.title("Diagonal")
# plt.xticks(range(num_samples), range(1, num_samples+1))
plt.ylim(0, 1.05)
plt.grid()

plt.show()




