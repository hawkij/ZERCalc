def ZERs_CheckInputs(Production_Matrix, q_System, Process_Shares):
    """
    Checks for known issues in the input data for the ZER model and returns diagnostic flags.

    This function performs a series of input checks on the production matrix, demand vector, and process shares 
    used in the Zero Emissions Resource (ZER) model. It verifies whether:
    - NETs (negative emissions technologies) are present and configured correctly
    - Process shares for each activity sum to one
    - Any activity has no process assigned (zero diagonal entry)
    - Circular dependencies exist between processes (making the system unsolvable)

    Parameters
    ----------
    Production_Matrix : pandas.DataFrame
        Activity-process-resource matrix of recipe coefficients, including both internal and external flows.
    
    q_System : pandas.DataFrame
        Demand vector specifying the required output of each activity or resource, typically from the user.
    
    Process_Shares : pandas.DataFrame
        Table of technology shares for each activity and process, used to scale the production matrix.

    Returns
    -------
    NETsMode : int
        1 if NetEmissions is included as an internal resource (NETs enabled), 0 if NETs are excluded.
    
    CircularityWarning : bool
        True (1) if circular process dependencies are detected (making the model unsolvable), False (0) otherwise.
    
    EmptyActivityWarning : bool
        True (1) if any activity has zero-valued diagonal entry (i.e., no process assigned), False (0) otherwise.
    
    IncompleteProcesses : list
        List of process names (activities) for which the process share does not sum to 1.0.
    """
    
   # import modules
    
    import pandas as pd
    import numpy as np
    
    # Select the resources which are external 
    selected_resources = ["BiomassCapacity", "CO2Storage", "NEElectricity"]
    
    # Split the production matrix into the internal and external resources to create the stacked matrices of P_System and P_Ext
    P_System = Production_Matrix.drop(selected_resources, axis = 0).sort_index(axis = 1).sort_index(axis = 0)
    np.savetxt("../Output/CSVs/matA.csv", P_System.values, delimiter=',')
    
    P_Ext = Production_Matrix.loc[selected_resources].sort_index(axis = 1)
    np.savetxt("../Output/CSVs/matB.csv", P_Ext.values, delimiter=',')
    

    ##################################### NETs mode? and delivery process shares ########################################
    
    # Check if NETs are used in the model and make the process an external flow if not (removing the process column from the A matrix)
    # This is needed to deal with 2018 verification runs but could be applied to any Activity and scenario
    # In the calculator we will have a different input to determine whether we remove NETs (there will be a toggle)
    
    # Default assumption is that we do have NETs (in this code, in the model it may be the other way around?)
    NETsMode = 1
    
    ProcessSharesCompleteness = 1
    IncompleteProcesses = []
    
    # If Process shares for NETs adds to zero, treat residual emissions like a ZER
    # Check that other Process shares all add to one
    P_System_diag = pd.DataFrame(np.diag(P_System.copy(deep = True)), index = P_System.index, columns=['DiagonalEntry'])
    # print(np.any(abs(P_System_diag) !=1))
    if np.any(abs(P_System_diag) != 1):
        ProcessSharesCompleteness = 0
        if np.any(P_System_diag[abs(P_System_diag['DiagonalEntry'])!=1].index== 'NetEmissions'):
            print("No NETs Mode")
            NETsMode =0
            selected_resources = ["BiomassCapacity", "CO2Storage", "NEElectricity", 'NetEmissions']
            P_Ext = Production_Matrix.loc[selected_resources].sort_index(axis = 1).drop('NetEmissions', axis = 1)
            P_System = Production_Matrix.drop(selected_resources, axis = 0).drop('NetEmissions', axis = 1)
            q_System = q_System.drop('NetEmissions', axis = 0)
            
            P_System_diag = pd.DataFrame(np.diag(P_System.copy(deep = True)), index = P_System.index, columns=['DiagonalEntry'])
            
        else:
            IncompleteProcesses = P_System_diag['DiagonalEntry'][abs(P_System_diag['DiagonalEntry'])!=1]
    
    EmptyActivityWarning = 0
    
    # now that NEts have been removed (if needed) check to see if any other activities have no processes assigned. Were this the case, the determinant would be zero and the model unsolvable
    if ProcessSharesCompleteness !=1:
        if np.any(abs(P_System_diag) == 0):
            EmptyActivityWarning = 1
        # np.savetxt("../Output/../Output/CSVs/matA2.csv", P_System.values, delimiter=',')
        
    ########################### CHECK FOR IMPOSSIBLE PROCESS COMBINATIONS (circularity) #############################################
    
    # need to firstly check for circularity and end the model, asking for a change in mode shares if there is
    # create a matrix to identify mutually dependent processes - this is not needed but a useful visual tool to understand the structure
    # P_System_structure = (P_System >0).astype(int)-(P_System<0).astype(int)
    
    # if any off-diagonal element of the Hadamard product of the Process matrix and its transpose ≥1 then there is circularity (an impossible model setup)
    P_System_sym = np.multiply(P_System, P_System.T)
    np.fill_diagonal(P_System_sym.values, 0,  wrap=False)
    CircularityWarning = np.any(P_System_sym>=1)
    CircularProcesses = [(P_System_sym.index[x], P_System_sym.columns[y]) for x,y in np.argwhere(P_System_sym.values >=1)]
    
    if CircularityWarning == 1:
        print("The combination of processes you’ve chosen for the following Activitys are impossible (they each depend on each other). Try changing your choice of technology for these Activitys:\n", 
              CircularProcesses)
         
    return NETsMode, CircularityWarning, EmptyActivityWarning, IncompleteProcesses
    
   