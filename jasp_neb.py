from jasp import *
from ase.io import read, write
'''
code for running NEB calculations in jasp

here is typical code to set up the band:

with jasp('../surfaces/Pt-slab-O-fcc') as calc:
    initial_atoms = calc.get_atoms()

with jasp('../surfaces/Pt-slab-O-hcp') as calc:
    final_atoms = calc.get_atoms()

images = [initial_atoms]
images += [initial_atoms.copy() for i in range(3)]
images += [final_atoms]

neb = NEB(images)
# Interpolate linearly the positions of the three middle images:
neb.interpolate()

with jasp('O-diffusion',
          ibrion=2,
          nsw=50,
          images=5,  # initial + nimages + final
          spring=-5,
          atoms=images) as calc:
          images, energies = calc.get_neb()

The spring tag triggers the setup of an NEB calculation for Jasp.

'''

def get_neb(self, npi=1):
    '''
    returns images, energies if available or runs the job

    npi = nodes per image for running the calculations
    '''

    # how do we know if we need to run jobs?
    '''
    if jobid exists that means it is queued

    if no jobid, and no OUTCAR for each image, then calculation required.

    if there is an OUTCAR in each image, but no jobid, we need to check for some
    convergence criteria in each image directory.
    '''
    calc_required = False

    if os.path.exists('jobid'):
        from jasp import VaspQueued
        raise VaspQueued

    # check for OUTCAR in each image dir
    for i in range(1, self.neb_nimages +1):
        wf = '0{0}/OUTCAR'.format(i)
        if not os.path.exists(wf):
            calc_required = True
            break
        else:
            # there was an OUTCAR, now we need to check for
            # convergence. if we cannot find convergence, it may be
            # necessary to restart the calculations.
            import warning
            warning.warn('No jobid found, and OUTCARS exist. check for convergence.')
            pass

    if calc_required:
        '''
        this creates the directories and files if needed.

        write out the poscar for all the images. write out the kpoints and
        potcar.
        '''

        for i,atoms in enumerate(self.neb_images):
            image_dir = '0{0}'.format(i)

            if not os.path.isdir(image_dir):
                # create if needed.
                os.makedirs(image_dir)
                write('{0}/POSCAR'.format(image_dir),atoms,format='vasp')

        if not os.path.exists('KPOINTS'):
            self.write_kpoints()

        if not os.path.exists('POTCAR'):
            # we need an atoms object to get a potcar. we use the initial state
            self.initialize(self.neb_images[0])
            self.write_potcar()

        if not os.path.exists('INCAR'):
            # we need an atoms object to get an incar
            self.write_incar(self.neb_images[0])

        if os.path.exists('jobid'):
            raise VaspQueued

        # run the job
        # what about an NEB metadata?
        #        if not os.path.exists('METADATA'):
        # we need atoms to write metadata!
        #   self.create_metadata()

        JASPRC['queue.nodes'] = npi*self.neb_nimages
        self.run() # this will raise VaspSubmitted


    #############################################
    # now we are just retrieving results
    images = [self.neb_images[0]]
    energies = [self.neb_initial_energy] #this is a tricky point. unless
                                     #the calc stores an absolute
                                     #path, it may be tricky to call
                                     #get_potential energy

    for i in range(1,nimages+1):
        nebd = '0{0}'.format(i)
        try:
            os.chdir(nebd)
            energies += [self.read_energy()[1]]
            atoms = read('CONTCAR',format='vasp')
            images += [atoms]
        finally:
            os.chdir('..')

    images += [self.images[-1]]
    energies += [self.neb_final_energy]

    return (images, energies)

Vasp.get_neb = get_neb

def plot_neb(self):
    '''
    retrieve the energies and atoms from the band
    '''
    images, energies = self.get_neb()

    # view
    from ase.visualize import view
    view(images)

    import matplotlib.pyplot as plt
    plt.plot(energies)
    plt.xlabel('Image')
    plt.ylabel('Energy (eV)')
    plt.show()

Vasp.plot_neb = plot_neb