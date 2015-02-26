#!/usr/bin/env python


def format_state(moddir,usevars, ftimes):
    """ Function to return an ensemble state from the models """
    from classes import Xray_Ensemble_State

    mems = moddir.keys()
    ntimes = len(ftimes)
    nmems = len(mems)
    nvars = len(usevars)
    nlocs = 1
    # Make an empty array for the state
    state = np.zeros((nvars,ntimes,nlocs,nmems))
    # Populate the state
    meta = {}
    meta[(0,'var')] = [None]*nvars
    meta[(1,'time')] = ftimes
    meta[(2,'location')] = ['KLGB']*nlocs
    meta[(3,'mem')] = [n+1 for n in xrange(nmems)]
    for varnum, var in enumerate(usevars):
        startdex = varnum * ntimes
        enddex = (varnum + 1) * ntimes
        meta[(0,'var')][varnum] = var
        # Loop through each member and populate its part of the state
        for memnum, member in enumerate(mems):
            if var == 'temp':
                varset = [moddir[member][t].tmpc for t in ftimes]
            elif var == 'dewp':
                varset = [moddir[member][t].dwpc for t in ftimes]
            elif var == 'uwnd':
                varset = [moddir[member][t].uwnd for t in ftimes]
            elif var == 'vwnd':
                varset = [moddir[member][t].vwnd for t in ftimes]
            elif var == 'psfc':
                varset = [moddir[member][t].press for t in ftimes]
            elif var == 'wspd':
                varset = [moddir[member][t].sknt for t in ftimes]
            elif var == 'precip':
                varset = [moddir[member][t].p01m for t in ftimes]
                varset[0] = 0.0
            elif var == 'cldfrac':
                varset = [moddir[member][t].cfrl for t in ftimes]
                varset[0] = 0.0
            #state[startdex:enddex,memnum] = varset
            state[varnum,:,0,memnum] = varset
    statecls = Xray_Ensemble_State(state=state, meta=meta)
    return statecls




def bufkit_parser(file):
    # Parses out the surface data from bufkit profiles
    # of various models.
    import re
    from datetime import datetime
    from classes import Profile
    import os

    # Load the file
    infile = open(file,'r')

    profile_dir = {}
    cur_profile = Profile()
    validtime = ''

    # Find the block that contains the description of
    # what everything is (header information)
    block_lines = []
    inblock = False
    for line in infile:
        if re.search('SELV',line):
            elev = re.search('SELV = (\d{1,4})',line).groups()[0]
            elev = float(elev)
        if line.startswith('STN YY'):
            # We've found the line that starts the header info
            inblock = True
            block_lines.append(line)
        elif inblock:
            # Keep appending lines until we start hitting numbers
            if re.match('^\d{6}',line):
                inblock = False
            else:
                block_lines.append(line)

    #print block_lines
    # Get the station elevation


    # Build an re search pattern based on this
    # We know the first two parts of the section are station id num and date
    re_string = "(\d{6}) (\d{6})/(\d{4})"
    # Now compute the remaining number of variables
    dum_num = len(block_lines[0].split()) - 2
    for n in range(dum_num):
        re_string = re_string + " (-?\d{1,4}.\d{2})"
    re_string = re_string + '\r\n'
    for line in block_lines[1:]:
        dum_num = len(line.split())
        for n in range(dum_num):
            re_string = re_string + '(-?\d{1,4}.\d{2}) '
        re_string = re_string[:-1]  # Get rid of the trailing space
        re_string = re_string + '\r\n'

    # If you want to see what the above code managed to put together
    # as a regular expression search pattern, uncomment this:
    #print re_string
    #raw_input()

    # Compile this re_string for more efficient re searches
    block_expr = re.compile(re_string)

    # Now get corresponding indices of the
    # variables we need
    full_line = ''
    for r in block_lines:
        full_line = full_line + r[:-2] + ' '
    # Now split it
    varlist = re.split('[ /]',full_line)

    # To see the variable list, uncomment
    #print varlist
    #raw_input()

    with open(file) as infile:
       # Now loop through all blocks that match the
       # search pattern we definied above
       for block_match in block_expr.finditer(infile.read()):
            #print "Match found"
            # For each match, make a fresh profile
            del cur_profile
            cur_profile = Profile()
            cur_profile.elev = elev
            # Split out the match into each component number
            vals = block_match.groups()
            # Set the time
            dt = '20' + vals[varlist.index('YYMMDD')] + vals[varlist.index('HHMM')]
            validtime = datetime.strptime(dt,'%Y%m%d%H%M')
            # Have to manually compute the wind

            # What's nice is because we made a list of variable names from the header
            # information that exactly matches the number of values we get after splitting
            # each matched block into its component numbers, the index of each variable name
            # in the varlist list corresponds with the index of the corresponding value in the
            # list of components in each block.  This makes the script flexible.  Also explains the
            # vals[varlist.index()]] notation--get the value from the index that matches the index of
            # the variable name we want
            uwind = float(vals[varlist.index('UWND')])
            vwind = float(vals[varlist.index('VWND')])
            wspd = sqrt(uwind**2 + vwind**2)
            cur_profile.sknt = wspd
            cur_profile.uwnd = uwind
            cur_profile.vwnd = vwind
            cur_profile.press = float(vals[varlist.index('PRES')])
            cur_profile.tmpc = float(vals[varlist.index('T2MS')])
            cur_profile.dwpc = float(vals[varlist.index('TD2M')])
            hcld = float(vals[varlist.index('HCLD')])
            mcld = float(vals[varlist.index('MCLD')])
            lcld = float(vals[varlist.index('LCLD')])
            cur_profile.cfrl = int((hcld + mcld + lcld) / 3.0)
            # Could be 3 hour or 1 hour precip -- store them both as p01m
            try:
                cur_profile.p01m = float(vals[varlist.index('P01M')])
            except:
                cur_profile.p01m = float(vals[varlist.index('P03M')])
            # Store the profile in the profile_dir, keyed by the valid time            
            profile_dir[validtime] = cur_profile

    #raw_input()
    return profile_dir



def get_sref_forecast(siteid):
    """ Load all the SREF member forecasts """
    import os
   
    # List all files we have
    filelist = [f for f in os.listdir('./static') if '.buf' in f]
    models = {}
    for filenm in filelist:
        modelid = filenm[5:-4]
        print("MODEL:", modelid)
        if modelid != 'srefmean':
            profile = bufkit_parser('./static/' + filenm)
            models[modelid] = profile
    # Find the times
    allmods = models.keys()
    testmod = models[allmods[0]]
    times = testmod.keys()
    times.sort()
    init_time = times[0]
    return models, init_time, times

