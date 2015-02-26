#!/usr/bin/env python

class Xray_Ensemble_State:
    """Define an ensemble state vector"""
    def __init__(self, state=None, meta=None, usevars=None, usedims=None):
        """ Initialize based on the input.  We are either given a
        netCDF4 "Dataset" object as "state" with a list of variables and dimensions
        to use OR we are given a numpy ndarray as a state with the variables and
        dimensions specified in the variable "meta" """
        
        if isinstance(state, Dataset):
            """ Read in the dataset here """
            pass
        
        else:
            meta_names = meta.keys()
            meta_names.sort()
            meta_titles = [m[1] for m in meta_names]
            # Be sure this matches the number of dimensions
            # In the array
            assert len(meta_titles) == len(state.shape)
            
            # Be sure that there is a dimension called
            # "mem" so that we know how to format the
            # state later for assimiation
            assert "mem" in meta_titles
            
            
            
            # Make sure that the 'mem' dimension is the
            # last one -- VERY IMPORTANT
            if meta_titles[-1] != 'mem':
                print("Dimension 'mem' is not the last dimension!")
                return None
            
            # We grab all the coordinate values from the
            # dictionary of metadata
            coords = [meta[m] for m in meta_names]
            # Make a DataArray (basically, a labeled
            # numpy ndarray) from the state data with
            # the dimensions and coordinate values specified
            # in "meta"
            self.state = xray.DataArray(state,
                                    dims=meta_titles,
                                    coords=coords)
            
            #Convert self.state to a Dataset instead?

        
    def state_to_array(self):
        """ Returns an array of the values in a shape of 
        Nstate x Nmems """
        # This assumes that the mems dimension is last
        return np.reshape(self.state.values,(self.num_state(), self.num_mems()))
    
    def update_state_from_array(self,instate):
        """ Takes an Nstate x Nmems ndarray and rewrites the state accordingly """
        instate = np.reshape(instate,self.shape())
        self.state.values = instate
    
    def shape(self):
        """ Returns the full shape of the DataArray """
        return self.state.shape
    
    def num_mems(self):
        """Returns number of ensemble members"""
        return self.state.coords['mem'].size
    
    def num_state(self):
        """Returns length of state vector"""
        coord_lengths = [s.shape for v,s in self.state.coords.items()]
        return np.product(coord_lengths)/self.num_mems()
    
    def ensemble_mean(self):
        """Returns the ensemble mean of the state as a DataArray"""
        return self.state.mean(dim='mem')
    
    def ensemble_perts(self):
        """Removes the ensemble mean and returns an Xray DataArray\
        of the perturbations from the ensemble mean"""
        #emean = self.ensemble_mean()
        return self.state - self.ensemble_mean()
        #return self.state.values


class Observation:
    def __init__(self,value=None,obtype=None,time=None,error=None,loc=None,
                 prior_mean=None, post_mean=None, prior_var=None, post_var=None):
        self.value = value
        self.obtype = obtype
        self.time = time
        self.error = error
        self.location = loc
        self.prior_mean = prior_mean
        self.post_mean = post_mean
        self.prior_var = prior_var
        self.post_var = post_var
        
    def H(self,state):
        """ Given an ensemble state class, compute an H """
        # Make an empty array filled with zeros
        state_shape = state.shape()
        H_values = np.zeros(state_shape[:-1]) # Ignore the members dimension
        #print(H_values.shape)
        #print(state_shape)

        # Now make a new DataArray of this zeros
        # array with the same dimensions as the state
        state_dims = state.state.coords
        state_dim_names = list(state.state.dims[:])
        # Remove the member dimension here
        state_dim_names.remove('mem')
        new_dims = {}
        for dname,dvals in state_dims.items():
            if dname != 'mem':
                new_dims[dname] = dvals
                
        # Make the data array
        H_da = xray.DataArray(H_values, coords=new_dims, dims=state_dim_names)
        
        # For now, we know our forward operator is an identity, just
        # find out where to place the "1.0" in H.  Could imagine more complicated
        # filtering and processing here based on location, time, etc.
        H_da.loc[dict(location=self.location.upper(), time=self.time, var=self.obtype)] = 1.0
        
        # Return a flattened array of length Nstate containing H
        return np.ravel(H_da.values)

    
    def H_Xb(self, state):
        """ Return the ensemble (state) estimate of the ob """
        # For now, just look up the coordinates of this in the state
        # Could make this a fully non-linear function of the state as long as
        # it returns an array of ensemble estimates for the observation
        values = state.state.sel(location = self.location.upper(), time=self.time, var=self.obtype)
        return values.values

class Profile:
    def __init__(self):
        # Initialize the variables that define the
        # profile
        self.model = ''
        self.valid_time = ''
        self.fcst_hour = ''
        self.stid = ''
        self.pres = ''
        self.alt = ''
        self.elev = ''
        self.tmpc = ''
        self.tmwc = ''
        self.dwpc = ''
        self.thte = ''
        self.drct = ''
        self.sknt = ''
        self.uwnd = ''
        self.vwnd = ''
        self.omeg = ''
        self.cfrl = ''
        self.hght = ''
        self.p01m = ''
        self.p03m = ''
        self.maxT = ''
        self.minT = ''


