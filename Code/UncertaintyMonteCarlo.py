"""
ZERs Monte Carlo Simulation and Analysis Script

This script runs a Monte Carlo analysis of the ZERs model by perturbing 
process coefficients using a normal distribution and evaluating 
the effects on model outputs (ZER demands).

Key Components:
---------------
1. **ZERs_MonteCarlo()**: 
   - Performs Monte Carlo iterations of the ZERs model.
   - Perturbs model coefficients and runs the ZERs system solver for each sample.
   - Collects model outputs (Biomass, CO2 Storage, NEE, Net Emissions).
   - Returns full results and flags whether all scenarios are net-zero.

2. **MonteCarlo_PMatrix()**:
   - Converts perturbed coefficients from a single iteration into a production matrix.
   - Useful for diagnosing problematic runs.

3. **Main Section**:
   - Specifies the model scenario (e.g., UK_2050, IEANZE).
   - Calls `ZERs_MonteCarlo()` with selected inputs.
   - Saves results to CSV for further analysis.

Inputs:
-------
- Excel file of model coefficients (e.g., "../Data/Recipe_Coefficients.xls")
- Tech share and demand scenario column names.
- Monte Carlo configuration: number of iterations and perturbation variance.

Outputs:
--------
- CSV: Monte Carlo model outputs (`monte_carlo_results_<scenario>_<var>.csv`)
- Optional: perturbed input sample causing model error for diagnostics.

Author:
-------
J Hawkin
"""

import pandas as pd
import numpy as np
from scipy.stats import norm


def ZERs_MonteCarlo(file, TechShare_ColName, Demand_ColName, Iterations, variance):
    """
    Performs Monte Carlo analysis of the ZERs model using normal distribution of the model coefficients for a given (fixed) set of model input values
        
        Parameters
        ----------
        file : string
            '.xls' file name e.g. "../Data/Recipe_Coefficients.xls".
        TechShare_ColName : string
            name of the col in TechShare_sheet_name which contains the proportions of each technology to be used for this run.
        Demand_ColName : string
            name of the col in Demand_sheet_name which contains the end-user demands of each Activity. NOTE: for the model to give correct solutions, this column cannot have non-zero values for intermediate Activitys
        Iterations: int
            number of iterations of monte carlo to be run
        Variance: float
            variance of the normal distribution used to represent uncertainty of all (non functional flow) model coefficients
        
        Returns
        -------  
        df_monte_carlo_results: 
            Dataframe of model output for each iteration of the model run
        NetZero: 
            False if any instance of the model runs is not net-zero emissions
    """
    ############################ IMPORT MODULES ################################
    
    
    ########################## ASSIGN RELEVANT FILE NAMES ######################
    excel_file = file
    # excel_file = "../Data/Recipe_Coefficients.xls"
    
    def monte_carlo_perturbation(coeff_df, variance=Variance, num_iterations=Iterations):
        
        """
        Function to generate random perturbations of non-functional flow model coefficients using normal distribution
            
            Parameters
            ----------
            coeff_df : Dataframe 
                Coefficients of non-functional flows, values for coefficients given in the 'Best_Estimate_Data' column. 
            
            variance: float
                Variance of the normally distributed pertubation applied to non-functional flow coefficients
            
            num_iterations: int
                Number of iterations
                
            Returns
            -------  
            perturbed_dfs: Dataframe 
                Perturbed non-functional flow coefficients 
                
                
        """
        perturbed_dfs = []
    
        # Iterate for each Monte Carlo simulation
        for _ in range(num_iterations):
            perturbed_df = coeff_df.copy() # start from the baseline non-functional flow coefficients 
    
            # Apply a normal distribution perturbation to each coefficient
            perturbations = norm.rvs(loc=1, scale=variance, size=len(perturbed_df)) # create an array of scaling factors normally distributed around 1, with a variance of 'variance'
            perturbed_df['Best_Estimate_Data'] *= perturbations # multiply the coeffients by the array of scaling factors
    
            # Append the perturbed dataframe to the list of other perturbed dataframes
            perturbed_dfs.append(perturbed_df)
        
        return perturbed_dfs
        
    def process_monte_carlo_perturbation(perturbed_coeffs, DF_Coeffs_FuncFlows):
        """
        Function to run the model for a single Monte Carlo perturbation
            
            Parameters
            ----------
            perturbed_coeffs : Dataframe 
                Perturbed non-functional flow coefficients 
            
            DF_Coeffs_FuncFlows: Dataframe
                Functional flow coefficients
                
            Returns
            -------  
            Bio, CS, NEE, NetEmissions: Floats 
                ZER demands for the given monte carlo run
                
                
        """
        Process_Coeffs = pd.concat([perturbed_coeffs, DF_Coeffs_FuncFlows]).sort_index() # add the functional flows back into the dataframe of perturbed non-functional flows
        Process_Coeffs = Process_Coeffs.pivot_table(values="Best_Estimate_Data", index=["Activity", "Process"], columns="Resource", fill_value=0) # reshape so that each column represents 
    
        Production_Matrix = Process_Coeffs.mul(Process_Shares.values, axis=0).groupby(level=0).sum().T
        (NETsMode, CicularityWarning, WarningEmptyActivity, IncompleteProcesses) = ZERs_CheckInputs(Production_Matrix, q_System, Process_Shares)
    
        # Check for warnings and return None if found
        if WarningEmptyActivity != 0 or CicularityWarning != 0:
            return None, None, None, None
    
        # Solve the model
        Solution = ZERs_FindRates(Production_Matrix, q_System, Process_Shares, NETsMode)
        s = Solution['s']
    
        # Select external resources
        if NETsMode == 0:
            selected_resources = ["BiomassCapacity", "CO2Storage", "NEElectricity", 'NetEmissions']
            P_Ext = Production_Matrix.loc[selected_resources].sort_index(axis=1).drop('NetEmissions', axis=1)
            P_System = Production_Matrix.drop(selected_resources, axis=0).drop('NetEmissions', axis=1)
        else:
            selected_resources = ["BiomassCapacity", "CO2Storage", "NEElectricity"]
            P_System = Production_Matrix.drop(selected_resources, axis=0).sort_index(axis=1).sort_index(axis=0)
            P_Ext = Production_Matrix.loc[selected_resources].sort_index(axis=1)
    
        # Calculate outputs
        q_model = np.matmul(P_System, np.asarray(s))
        u_ZER = np.matmul(P_Ext, np.asarray(s))
    
        Bio = u_ZER.loc['BiomassCapacity'].iloc[0] * -1
        CS = u_ZER.loc['CO2Storage'].iloc[0]
        NEE = u_ZER.loc['NEElectricity'].iloc[0] * -1
    
        if NETsMode == 1:
            NetEmissions = round(q_model.loc['NetEmissions', 0], 3)
        else:
            NetEmissions = round(u_ZER.loc['NetEmissions'].iloc[0], 3)
    
        return Bio, CS, NEE, NetEmissions
 
    
    # Assign Model Coefficients
    DF_Coeffs = pd.read_excel(excel_file, "Coefficients", index_col='ID')
    
    from FunExtractInputs import ZERS_LoadInputs
    from FunCheckInputs import ZERs_CheckInputs
    from FunFindRates import ZERs_FindRates
    
    # Load the necessary inputs for the base case run
    Process_Coeffs_Orig, q_System, Process_Shares = ZERS_LoadInputs(excel_file, TechShare_ColName, Demand_ColName)
    
    # Split the dataframe into the coefficients for the functional flows and coefficients for other inputs/outputs
    DF_Coeffs_FuncFlows = DF_Coeffs[DF_Coeffs['Resource']==DF_Coeffs['Activity']]
    DF_Coeffs_NoFuncFlows = DF_Coeffs[DF_Coeffs['Resource']!=DF_Coeffs['Activity']]
    
    ####### MONTE CARLO

    # Generate Monte Carlo perturbations
    monte_carlo_dfs = monte_carlo_perturbation(DF_Coeffs_NoFuncFlows, variance, Iterations)
    
    # Store results
    sensitivity_results = []
   
    # Main Monte Carlo loop
    for i, perturbed_coeffs in enumerate(monte_carlo_dfs):
        print(f"Monte Carlo Iteration {i}")
    
        # Process Monte Carlo perturbation
        Bio, CS, NEE, NetEmissions = process_monte_carlo_perturbation(perturbed_coeffs, DF_Coeffs_FuncFlows)
    
        if Bio is None:  # If a warning or error occurred, skip this iteration
            print(f"Iteration {i} caused a model warning. Skipping.")
            continue
    
        # Append results
        sensitivity_results.append({
            'Iteration': i,
            'Bio': Bio,
            'CS': CS,
            'NEE': NEE,
            'NetEmissions': NetEmissions
        })
    
    # Convert results to DataFrame for analysis
    df_monte_carlo_results = pd.DataFrame(sensitivity_results)
    
    NetZero = True
    
    # Check emissions are all zero
    if np.any(df_monte_carlo_results.NetEmissions != 0):
        NetZero = False
        print("Warning, one of the model runs was not net-zero emissions.")
        
    return monte_carlo_dfs, df_monte_carlo_results, NetZero

def MonteCarlo_PMatrix(excel_file, TechShare_ColName, Demand_ColName, perturbed_coeffs):
    """
    Function to transform a dataframe of perturbed monte carlo non-functional flow coefficients into a production matrix (to be able to understand why some do not solve)
    
    
    """
    
    # Assign Model Coefficients
    DF_Coeffs = pd.read_excel(excel_file, "Coefficients", index_col='ID')
    
    from FunExtractInputs import ZERS_LoadInputs

    
    # Load the necessary inputs for the base case run
    Process_Coeffs_Orig, q_System, Process_Shares = ZERS_LoadInputs(excel_file, TechShare_ColName, Demand_ColName)
    
    # Split the dataframe into the coefficients for the functional flows and coefficients for other inputs/outputs
    DF_Coeffs_FuncFlows = DF_Coeffs[DF_Coeffs['Resource']==DF_Coeffs['Activity']]
    
    Process_Coeffs = pd.concat([perturbed_coeffs, DF_Coeffs_FuncFlows]).sort_index() # add the functional flows back into the dataframe of perturbed non-functional flows
    Process_Coeffs = Process_Coeffs.pivot_table(values="Best_Estimate_Data", index=["Activity", "Process"], columns="Resource", fill_value=0) # reshape so that each column represents 

    Production_Matrix = Process_Coeffs.mul(Process_Shares.values, axis=0).groupby(level=0).sum().T
    
    return Process_Coeffs, Production_Matrix


Iterations  = 1000
Variance = 0.1
file = "../Data/Recipe_Coefficients.xls"

# # AccumulatedDemands
TechShare_col_name = 'TechShare2050'
Demand_col_name = '2050 Process Rate'
runtype = 'Accumulated'

#Electrification dominant
#TechShare_col_name = 'UK_2050'
#Demand_col_name = '2050 Process Rate'
#runtype = 'UK_2050'

# # inputs for the low energy and material demand scenario
# runtype = 'Low-ZER'
# Demand_col_name = 'LZERD_NEEBudget'
# TechShare_col_name = 'LZERD'

# # inputs for IEA net-zero by 2050 run
# runtype = 'IEANZE'
# Demand_col_name = 'IEANZE Process Rate'
# TechShare_col_name = 'IEANZE'

# runtype = 'Yr2018'
# TechShare_col_name = 'Yr_2018'
# Demand_col_name = 'Yr_2018'

df_monte_carlo_inputs, df_monte_carlo_results, NetZero = ZERs_MonteCarlo(file, TechShare_col_name, Demand_col_name, Iterations, Variance)

# Save to CSV if needed
df_monte_carlo_results.to_csv("../Output/MonteCarlo/monte_carlo_results_"+ runtype+ "_"+ str(round(Variance*100))+".csv", index=False)
# df_monte_carlo_inputs[1466].to_csv("../Output/MonteCarlo/monte_carlo_inputs_"+ runtype+ "_"+ str(round(Variance*100))+".csv", index=False)



############# error searching




# ProcessCoeffs_1466, P_Mat_1466 = MonteCarlo_PMatrix(file, TechShare_col_name, Demand_col_name, df_monte_carlo_inputs[1466])