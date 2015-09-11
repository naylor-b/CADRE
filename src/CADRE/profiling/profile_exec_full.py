""" Optimization of the CADRE MDP."""

from __future__ import print_function

import numpy as np

from openmdao.core.mpi_wrap import MPI
from openmdao.core.problem import Problem
from openmdao.drivers.pyoptsparse_driver import pyOptSparseDriver

if MPI:
    from openmdao.core.petsc_impl import PetscImpl as impl
else:
    impl = None

from openmdao.solvers.ln_gauss_seidel import LinearGaussSeidel
from openmdao.solvers.petsc_ksp import PetscKSP

from CADRE.CADRE_mdp import CADRE_MDP_Group


# These numbers are for the CADRE problem in the paper.
n = 1500
m = 300
npts = 6

# Instantiate
model = Problem(impl=impl)
root = model.root = CADRE_MDP_Group(n=n, m=m, npts=npts)

# Add parameters and constraints to each CADRE instance.
names = ['pt%s' % i for i in range(npts)]
for i, name in enumerate(names):

    # add parameters to driver
    model.driver.add_param("%s.CP_Isetpt" % name, low=0., high=0.4)
    model.driver.add_param("%s.CP_gamma" % name, low=0, high=np.pi/2.)
    model.driver.add_param("%s.CP_P_comm" % name, low=0., high=25.)
    model.driver.add_param("%s.iSOC" % name, indices=[0], low=0.2, high=1.)

    model.driver.add_constraint('%s_con1.val'% name)
    model.driver.add_constraint('%s_con2.val'% name)
    model.driver.add_constraint('%s_con3.val'% name)
    model.driver.add_constraint('%s_con4.val'% name)
    model.driver.add_constraint('%s_con5.val'% name, ctype='eq')

# Add Parameter groups
model.driver.add_param("bp1.cellInstd", low=0., high=1.0)
model.driver.add_param("bp2.finAngle", low=0., high=np.pi/2.)
model.driver.add_param("bp3.antAngle", low=-np.pi/4, high=np.pi/4)

# Add objective
model.driver.add_objective('obj.val')

# For Parallel exeuction, we must use KSP
#model.root.ln_solver = PetscKSP()
#model.root.ln_solver = LinearGaussSeidel()

model.setup()
model.run()

#----------------------------------------------------------------
# Below this line, code I was using for verifying and profiling.
#----------------------------------------------------------------
params = model.driver.get_params().keys()
unks = model.driver.get_objectives().keys() + model.driver.get_constraints().keys()

import cProfile
import pstats

def zzz():
    # Set this range to higher to make the run longer.
    for j in range(1):
        model.run()

cProfile.run("zzz()", 'profout')

cProfile.run("model.calc_gradient(params, unks, mode='rev', return_format='dict')", 'profout')

p = pstats.Stats('profout')
p.strip_dirs()
p.sort_stats('cumulative', 'time')
p.print_stats()
print('\n\n---------------------\n\n')
p.print_callers()
print('\n\n---------------------\n\n')
p.print_callees()