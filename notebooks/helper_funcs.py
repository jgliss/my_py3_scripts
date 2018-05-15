"""Helper methods for notebooks"""
from pandas import DataFrame
import numpy as np
import xlrd
import matplotlib.cm as colormaps
import matplotlib.colors as colors
    
def shifted_color_map(vmin, vmax, cmap = None):
    """Shift center of a diverging colormap to value 0
    
    .. note::
    
        This method was found `here <http://stackoverflow.com/questions/
        7404116/defining-the-midpoint-of-a-colormap-in-matplotlib>`_ 
        (last access: 17/01/2017). Thanks to `Paul H <http://stackoverflow.com/
        users/1552748/paul-h>`_ who provided it.
    
    Function to offset the "center" of a colormap. Useful for
    data with a negative min and positive max and if you want the
    middle of the colormap's dynamic range to be at zero level
    
    :param vmin: lower end of data value range
    :param vmax: upper end of data value range
    :param cmap: colormap (if None, use default cmap: seismic)
    
    :return: 
        - shifted colormap
        
    """

    if cmap is None:
        cmap = colormaps.seismic
    elif isinstance(cmap, str):
        cmap = colormaps.get_cmap(cmap)

    midpoint = 1 - abs(vmax)/(abs(vmax) + abs(vmin))
    cdict = {
        'red': [],
        'green': [],
        'blue': [],
        'alpha': []
    }

    # regular index to compute the colors
    reg_index = np.linspace(0, 1, 257)

    # shifted index to match the data
    shift_index = np.hstack([
        np.linspace(0.0, midpoint, 128, endpoint=False), 
        np.linspace(midpoint, 1.0, 129, endpoint=True)
    ])

    for ri, si in zip(reg_index, shift_index):
        r, g, b, a = cmap(ri)

        cdict['red'].append((si, r, r))
        cdict['green'].append((si, g, g))
        cdict['blue'].append((si, b, b))
        cdict['alpha'].append((si, a, a))

    return colors.LinearSegmentedColormap('shiftedcmap', cdict)

def read_var_info_michaels_excel(xlspath):
    """Read short description strings for variables
    
    The strings are available for some of the variables in Michaels analysis
    excel table (column 3, sheet "DATA")
    
    Parameters
    ----------
    xlspath : location of excel spreadsheet
    
    Returns
    -------
    dict 
        dictionary containing all variable names (keys) and corresponding
        description strings (if applicable, else empty string)
    """
    workbook = xlrd.open_workbook(xlspath)
    sheet = workbook.sheet_by_name('DATA')
    
    result = {}
    for i, cell in enumerate(sheet.col(1)):
        if cell.value:
            result[cell.value] = sheet.col(2)[i].value
       
    return result

def read_file_custom(fpath, var_info_dict=None, verbose=False):
    """Custom ASCII conversion method 
    
    Parameters
    ----------
    fpath : str
        path to file location
    var_info_dict : dict
        optinal dictionary that contains description strings for each of the 
        variables (e.g. retrieved using :func:`read_var_info_michaels_excel`)
    verbose : bool
        if True, print output (defaults to False)
    Returns
    -------
    Dataframe 
        pandas data frame ready for further analysis
    """
    with open(fpath, encoding="latin-1") as f:
        lines = f.read().splitlines()
    test_case = ''
    control_case = ''
    
    if not var_info_dict:
        var_info_dict = {}
    data = []

    in_data = False
    problem_vars = ["FSNTOAC_CERES-EBAF","FSNTOA_CERES-EBAF"]
    for line in lines:
        line.strip()
        
        if "TEST CASE:" in line:
            spl = line.split("TEST CASE:")[1].strip().split("(yrs ")
            test_case = spl[0]
            years = spl[1].split(")")[0]
            header = ["Run", "Years", "Variable", "Description", "Flag",
                      "Model", "Obs", "Bias", "RMSE"]
        elif "CONTROL CASE:" in line:
            control_case = line.split("CONTROL CASE:")[1].strip()
        elif "Variable" in line:
            in_data =True
        elif in_data:
            line_data = []
            is_problem_var = False
            for var in problem_vars:
                if var in line:
                    spl = line.split(var)
                    is_problem_var = True
                    _var = var
                    if verbose:
                        print("Problem case {}".format(_var))
            if is_problem_var:
                spl = spl[1].split()
            else:
                spl = line.split()
                _var = spl.pop(0)
            if len(spl) == 4:
                line_data.extend([test_case, years, _var])
                try:
                    var_info = var_info_dict[_var]
                    if not var_info:
                        raise ValueError("No description available for "
                                         "variable {}".format(_var))
                    flag = True
                except:
                    var_info = ""
                    flag = False
                line_data.extend([var_info, flag])  
                for item in spl:
                    val = float(item)
                    if val == -999:
                        val = np.nan
                    line_data.append(val)
                data.append(line_data)
        else:
            if verbose:
                print("Ignoring line: {}".format(line))
                #variables.append(_var)
    df = DataFrame(data, columns=header)
    df.set_index(["Run", "Years", "Variable", "Description"], 
                 inplace=True)
    if verbose:
        print("Test case: {}".format(test_case))
        print("Control case: {}".format(control_case))
    return df

if __name__ == "__main__":
    import os
    import pandas as pd
    
    data_dir = "./data/michael_ascii_read/"
    files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if 
             f.endswith(".webarchive")]
    
    df0 = read_file_custom(files[0])
    df1 = read_file_custom(files[1])
    
    concat = pd.concat([df0, df1], axis=0)
    df0.head()
    
    from glob import glob
    
    xlspath = glob("./data/michael_ascii_read/*.xlsx", recursive=True)[0]
    
    var_info = read_var_info_michaels_excel(xlspath)
    
    df2 =  read_file_custom(files[3])
    
    
    
    
    
    
    