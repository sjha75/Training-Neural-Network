from curses.ascii import GS
import matplotlib.pyplot as plt 
import numpy as np 
import torch 
from ase import Atoms 
import ase.io 
from ase.calculators.emt import EMT 
from ase.build import molecule 

from amptorch.ase_utils import AMPtorch
from amptorch.trainer import AtomsTrainer


training = ase.io.read("./training_data.traj", index=":-15:")
print(f"Length of training:  {len(training)}")

nsigmas = 10
sigmas = np.linspace(0, 2.0, nsigmas + 1, endpoint = True) [1:]

MCSHs_index = 2
MCSHs_dict = {
0: { "orders": [0], "sigmas": sigmas,},
1: { "orders": [0,1], "sigmas": sigmas,},
2: { "orders": [0,1,2], "sigmas": sigmas,},
3: { "orders": [0,1,2,3], "sigmas": sigmas,},
4: { "orders": [0,1,2,3,4], "sigmas": sigmas,},
5: { "orders": [0,1,2,3,4,5], "sigmas": sigmas,},
6: { "orders": [0,1,2,3,4,5,6], "sigmas": sigmas,},
7: { "orders": [0,1,2,3,4,5,6,7], "sigmas": sigmas,},
8: { "orders": [0,1,2,3,4,5,6,7,8], "sigmas": sigmas,},
9: { "orders": [0,1,2,3,4,5,6,7,8,9], "sigmas": sigmas,},
}

MCSHs = MCSHs_dict[MCSHs_index]
GMP = {
    "MCSHs" : MCSHs, 
    "atom_gaussians": {
        "H": "./valence_gaussians/H_pseudodensity_2.g",
        "O": "./valence_gaussians/O_pseudodensity_4.g",
    }, 
    "cutoff": 12.0,
    "solid_harmonics" : True,
}

elements = ["H", "O"]
config = {
    "model": {
        "name": "singlenn",
        "get_forces": True, 
        "num_layers": 3, 
        "num_nodes": 10, 
        "batchnorm": True,
        "activation": torch.nn.Tanh,
    }, 
    "optim": {
        "force_coefficient" : 0.01,
        "lr" : 1e-3,
        "batch_size" : 16, 
        "epochs" : 500,
        "loss" : "mse",
        "metric" : "mae",
    }, 
    "dataset": {
        "raw_data" : training, 
        "fp_scheme" : "gaussian",
        "fp_params" : GMP,
        "elements" : elements,
        "save_fps" : True, 
        "scaling" : {"type": "normalize", "range": (0, 1)},
        "val_split" : 0.1, 
    }, 
    "cmd" : {
        "debug": False, 
        "run_dir": "./",
        "seed" : 1,
        "identifier" : "test", 
        "verbose": True, 
        "logger": False,
    },
}

torch.set_num_threads(1)
trainer = AtomsTrainer(config)
trainer.train()

test = ase.io.read("./training_data.traj", index = "-15::")

print(f"Length of test dataset: {len(test)}")
predictions = trainer.predict(test)

true_energies = np.array([image.get_potential_energy() for image in test])
pred_energies = np.array(predictions["energy"])

print("Energy MAE:", np.mean(np.abs(true_energies - pred_energies)))

training[0].set_calculator(AMPtorch(trainer))
training[0].get_potential_energy()
