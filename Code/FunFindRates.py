def ZERs_FindRates(Production_Matrix, q_System, Process_Shares, NETsMode):
    """
    Solves for the process activity rates that meet user-specified demand using matrix inversion and fallback elimination.

    This function calculates the rates at which each process must operate to meet final demand, 
    as defined in `q_System`. It first attempts a matrix inversion solution, and if any rates 
    are negative (non-physical), it iteratively removes problematic processes and re-solves 
    using a fallback elimination method. Surpluses and iteration logs are recorded.

    Parameters
    ----------
    Production_Matrix : pandas.DataFrame
        Activity-resource matrix containing recipe coefficients, with rows as resources 
        and columns as activities, already scaled by technology shares.

    q_System : pandas.DataFrame
        Vector of demand values for each final product or service. Should not include intermediates.

    Process_Shares : pandas.DataFrame
        Table of technology shares (used to build the Production_Matrix, but not directly modified here).

    NETsMode : int
        Binary flag: 1 if NetEmissions is treated as an internal process (NETs included), 
        0 if NetEmissions is excluded and treated externally.

    Returns
    -------
    Results : dict
        A dictionary with the following keys:
        
        - 's' : pandas.DataFrame
            Final DataFrame of activity rates (i.e., how much each process runs). Negative rates are removed.
        
        - 'Surplus' : list of pandas.DataFrame or None
            List of DataFrames showing surplus or shortfall for each activity at each iteration 
            of the elimination method. Set to None if no fallback was needed (i.e., solution was physical).
    """

    ############################ IMPORT MODULES ################################
    
    import pandas as pd
    import numpy as np

    # The results are returned in a dictionary - initialise that here
    Results={}
    
    # Select the resources which are external  
    if NETsMode == 0:
        selected_resources = ["BiomassCapacity", "CO2Storage", "NEElectricity", 'NetEmissions']
        P_Ext = Production_Matrix.loc[selected_resources].sort_index(axis = 1).drop('NetEmissions', axis = 1)
        P_System = Production_Matrix.drop(selected_resources, axis = 0).drop('NetEmissions', axis = 1)
        q_System = q_System.drop('NetEmissions', axis = 0)
    else:
        selected_resources = ["BiomassCapacity", "CO2Storage", "NEElectricity"]
        # Split the production matrix into the internal and external resources to create the stacked matrices of P_System and P_Ext
        P_System = Production_Matrix.drop(selected_resources, axis = 0).sort_index(axis = 1).sort_index(axis = 0)
        # np.savetxt("../Output/CSVs/matA.csv", P_System.values, delimiter=',')
        P_Ext = Production_Matrix.loc[selected_resources].sort_index(axis = 1)
        # np.savetxt("../Output/CSVs/matB.csv", P_Ext.values, delimiter=',')
    ##################### SOLVE as an equality if the A matrix has an inverse #########################
    
    # Find the determinant of A to check there is an inverse
    P_System_det = np.linalg.det(P_System)
    
    if P_System_det  != 0:
    
        # Matrix inverse of A
        P_System_inv = np.linalg.inv(P_System)
        np.savetxt("../Output/CSVs/Inverse.csv", P_System_inv, delimiter=",")
        
        # Finding B*A^-1
        Lambda = np.matmul(-P_Ext, P_System_inv).sort_index(axis = 1).sort_index(axis = 0)
        np.savetxt("../Output/CSVs/Lambda.csv", Lambda, delimiter=",")
        
        s = pd.DataFrame(np.matmul(P_System_inv, q_System.values), index = q_System.index)
        s.columns = ["Model Rate"]
        
        # Not needed for the model - used for verification comparisons
        # ProductBiomass_Textiles = -1*(ResourceDemandPerActivity.loc['FarmedBiomass', 'Textiles']+ResourceDemandPerActivity.loc['Wood', 'Textiles'])
        # ProductBiomass_Paper = -1*ResourceDemandPerActivity.loc['Wood', 'Paper']
        # ProductBiomass_Construction = -1*ResourceDemandPerActivity.loc['Wood', 'Construction']
        # ProductBiomass_Total = ProductBiomass_Textiles + ProductBiomass_Paper + ProductBiomass_Construction
        # ProductFoodBiomass_Food = -1*ResourceDemandPerActivity.loc['FarmedBiomass', 'RawFood']
        # ProductFoodBiomass_Total = ProductFoodBiomass_Food + ProductBiomass_Total
        
        
    ######################### MATRIX INVERSE RESULTS ########################################
    
        # u_ZER = np.matmul( P_Ext, np.asarray(s))
        # # u_ZER.index = ['Bio', 'CS', 'NEE', 'Emissions']
        
        q_model = np.matmul( P_System, np.asarray(s))
        Surplus = round(pd.DataFrame(q_model.values - q_System.values, index = q_System.index), 6)
        
        # print('Matrix inverse solution: \n', -u_ZER, '\n')
        print("Matrix inverse solution minimum process rate is ", round(min(s['Model Rate']), 2), '\n')
        
       
        # # Assign each of the elements of the output
        # Bio = u_ZER.loc['BiomassCapacity'].iloc[0]*-1
        # CS = u_ZER.loc['CO2Storage'].iloc[0]
        # NEE = u_ZER.loc['NEElectricity'].iloc[0]*-1
    
        # if NETsMode == 1:
        #     NetEmissions = q_model.loc['NetEmissions', 0]    
        # else: 
        #     NetEmissions = u_ZER.loc['NetEmissions'].iloc[0]
            
        # print('Emissions are:', round(NetEmissions, 2), 'Gt CO2e')
        # print('Biomass demand is:', round(Bio, 1), 'Gt')
        # print('NEE demand is:', round(NEE, 0), 'EJ')
        # print('Carbon Storage demand is:', round(CS, 2), 'Gt CO2')
        
        
    # If all s (process rates) are >=0 then we do not need to use the elimination method and so we can stop the script 

    # Rounding is used to hide appearance of precision errors in the matrix inversion calculation
    # Adding 0 avoids the floating point/negative zero issue: https://stackoverflow.com/questions/4083401/negative-zero-in-python
    s = round(s, 6) + 0
    
    if np.all(s>=0):
        Results['Surplus'] = None
        Results['s'] = s
        return Results
    
    
    ########################### ELIMINATION METHOD #######################################
 
    # If any s<0 then the model is not operating physically and so we need to use the elimination method
        
    x = 1 # set up a loop iteration variable (to avoid very long iterations)
    # Initialise empty lists to store the rates and names of non-physical activities
    s_iterations = [] # A dataframe of Process rates calculated by each iteration
    NonPhysicalRateActivitys = [[]] # A list of lists of activities which have negative process rates in each iteration
    InsuffiicientActivities = [] # A list of activities which have non-phyiscal surplus (positive for waste, negative for )
    SurplusLog = [] # A list of list of activities' surplus rate
    InsufficiencyFlagLog = [] # List of the sufficiency status for each iteration (whether any process is running at an insufficient rate to meet the user-demanded input value))
    # The sign of the diagonal of the production matrix can be used to identify if the process is a production process (+ve) or a waste management process (-ve). This is needed to understand if we are meeting the user input demands.
    P_System_diag = pd.DataFrame(np.diag(P_System.copy(deep = True)), index = P_System.index, columns=['DiagonalEntry'])
    
 
    # Find which Activitys are running backwards
    NonPhysicalRateActivitys.append(s[s['Model Rate']<0].index)
 
    # In an iterative way, check for non-physical processes (negative surplus for production processes and positive surplus for waste management processes)
    # Remove non-physical processes from  the internal system, resolve and then check that sufficient service is being provided
    # If not, the processes need to be added back in
    for x in range(1, 10):
        InsufficiencyFlag = False
        
        print('\nIterative loop: ', x)
        # print(NonPhysicalRateActivitys)
        print('Min surplus is', min(Surplus.iloc[:, 0]),  ' for ', Surplus.idxmin())
        # Remove rows and columns relating to negative rates
        A_Truncated = P_System.drop(NonPhysicalRateActivitys[x-1], axis =0).drop(NonPhysicalRateActivitys[x-1], axis =1)
        q_Truncated = q_System.drop(NonPhysicalRateActivitys[x-1])

 
        # print('Removed Activitys: ', NonPhysicalRateActivitys[x-1])
 
        # find Matrix inverse of the new A, A_Truncated, and solve for s_Truncated
        A_inv_Truncated = np.linalg.inv(A_Truncated)
        s_Truncated = pd.DataFrame(np.matmul(A_inv_Truncated, q_Truncated.values), index = q_Truncated.index)
       # Rounding is used to hide appearance of precision errors in the matrix inversion calculation
        # Adding 0 avoids the floating point/negative zero issue: https://stackoverflow.com/questions/4083401/negative-zero-in-python
        s_Truncated = round(s_Truncated, 6) + 0
        
        s_Truncated.columns = ["Model Rate"]
        
        # Add back in the negative rate rows to check that the surplus is postive
        New_rows = pd.DataFrame({'Model Rate': 0}, index=NonPhysicalRateActivitys[x-1])
        

        s_Check = pd.concat([s_Truncated.copy(deep=True), New_rows]).sort_index(axis = 0)
        s_iterations.append(s_Check)
        
        New_q_model = np.matmul( P_System, np.asarray(s_Check))
        # Calculate the surplus (the difference between the demanded quantity and the delivered quantity of each Activity)).
        # This is the equivalent of q - q^ so should be >=0 for production processes, <=0 for waste management processes
        # Rounding is used to hide appearance of precision errors in the matrix inversion calculation
        # Adding 0 avoids the floating point/negative zero issue: https://stackoverflow.com/questions/4083401/negative-zero-in-python
        Surplus = round(pd.DataFrame(New_q_model.values - q_System.values, index = q_System.index, columns = ['Surplus']), 6) + 0
        SurplusLog.append(Surplus)
        
        
        # Check if any production process has an 'unphysical' surplus, set a flag if such a situation exists, identify and recording the specific production processes with a shortfall in InsuffiicientActivities 
        ProdIndex = P_System_diag[P_System_diag.DiagonalEntry==1].index
        WasteIndex = P_System_diag[P_System_diag.DiagonalEntry==-1].index
        print(WasteIndex)
        if any(Surplus.loc[ProdIndex].loc[Surplus['Surplus'] < 0]):
            InsufficiencyFlag = 'Production process negative surplus'
            # Identify negative surplus values corresponding to ProdIndex
            if InsuffiicientActivities is None:
                InsuffiicientActivities = []
            InsuffiicientActivities.append(Surplus.loc[ProdIndex].loc[Surplus['Surplus'] < 0].index)
        else:
            InsufficiencyFlag = False
 
        if any(Surplus.loc[WasteIndex, 'Surplus']>0):
            if InsufficiencyFlag == 'Production process negative surplus':
                InsufficiencyFlag = "Both negative production and positive waste surplus"
                InsuffiicientActivities = InsuffiicientActivities.append(Surplus.loc[WasteIndex].loc[Surplus['Surplus'] > 0].index)
            else:
                InsufficiencyFlag = 'Waste process positive surplus'
                InsuffiicientActivities = Surplus.loc[WasteIndex].loc[Surplus['Surplus'] > 0].index
        else:
            InsufficiencyFlag = False
     
        InsufficiencyFlagLog.append(InsufficiencyFlag)    
 
        if InsufficiencyFlag== False and np.all(s_Check>=0):
            break
 
 
        if np.all(s_Check>=0):
            # NonPhysicalRateActivitys.append(NonPhysicalRateActivitys[x-1].difference(InsuffiicientActivities[x-1]))
            # NonPhysicalRateActivitys.append([item for item in NonPhysicalRateActivitys[x-1] if item not in InsuffiicientActivities])
                # Ensure fallback to empty lists if either is None
            previous_non_physical = NonPhysicalRateActivitys[x-1] if NonPhysicalRateActivitys[x-1] is not None else []
            insufficient = InsuffiicientActivities if InsuffiicientActivities is not None else []
            
            # Apply difference-like operation on lists
            NonPhysicalRateActivitys.append([item for item in previous_non_physical if item not in insufficient])
        else:
            NonPhysicalRateActivitys.append(s_Check[s_Check['Model Rate']<0].index)


    ######################### ELIMINATION METHOD RESULTS ########################################
    
    s_iterations = pd.concat(s_iterations, axis = 1)

    Results['Surplus'] = SurplusLog
    Results['s'] = s_Check
    
    return Results
    
   