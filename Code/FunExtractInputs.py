def ZERS_LoadInputs(file, TechShare_ColName, Demand_ColName):
    """
    Loads and processes model input data from an Excel file for the ZERS system model.

    This function reads in the technology share data, end-use demand, and process 
    coefficients from the specified Excel file. It processes the data into the correct 
    format for use in the ZERS model, including pivoting and scaling of coefficients, 
    and saving intermediate outputs to CSV files for checking and debugging.

    Parameters
    ----------
    file : str
        Path to the Excel workbook containing the input data 
        (e.g., "../Data/Recipe_Coefficients.xls").
    
    TechShare_ColName : str
        Name of the column in the "TechShares" sheet that specifies the proportion 
        of each technology to be used for this model run.
    
    Demand_ColName : str
        Name of the column in the "Demand" sheet that contains the final demand values 
        for each end-use activity. 
        Note: This column must contain zero values for intermediate activities, or 
        the model may return incorrect solutions.

    Returns
    -------
    Process_Coeffs : pandas.DataFrame
        A pivoted matrix of activity-process-resource recipe coefficients, 
        scaled according to the specified technology shares.

    q_System : pandas.DataFrame
        A DataFrame containing the end-user demand vector, with NaNs replaced by zeros 
        and sorted by activity.

    Process_Shares : pandas.DataFrame
        A pivoted DataFrame of technology shares indexed by activity and process.
    """
 
    ############################ IMPORT MODULES ################################
    
    import pandas as pd
    import numpy as np
    # from scipy.optimize import linprog
    # import networkx as nx
    # from numpy.linalg import matrix_rank
    
    ########################## ASSIGN RELEVANT FILE NAMES ######################
    
    excel_file = file
    
    TechShare_SheetName = "TechShares" # name of the sheet in file which contains the proportions of each technology
    Demand_SheetName = "Demand" # name of the sheet in file which contains the end-user demands of each Activity.
    
    output_csv_demand = "..\Output\CSVs\EndUse_Demand.csv"
    output_csv_coeffs = "..\Output\CSVs\Process_Coeffs.csv"
    output_csv_scaling = "..\Output\CSVs\Process_Shares.csv"
   
    
    ################### EXTRACT DATA ##########################################
    
    # Assign Demand
    EndUse_Demand = pd.read_excel(excel_file, Demand_SheetName, index_col="Activity")[Demand_ColName].sort_index()
    
    #EndUse_Demand.to_csv(output_csv_demand)
    saving1 = EndUse_Demand.values
    np.savetxt("../Output/CSVs/Demand1.csv", saving1, delimiter=',')
    
    # Assign Model Coefficients
    DF_Coeffs = pd.read_excel(excel_file, "Coefficients", index_col='ID')
    Process_Coeffs = DF_Coeffs.pivot_table(values="Best_Estimate_Data", index=["Activity", "Process"], columns="Resource", fill_value=0)
    #Process_Coeffs.to_csv(output_csv_coeffs)
    saving2 = Process_Coeffs.values
    np.savetxt("../Output/CSVs/Coeffs1.csv", saving2, delimiter=',')
    
    
    # Assign Scaling Factors
    DF_Scaling_Factors = pd.read_excel(excel_file, TechShare_SheetName, index_col='Activity_Process')
    Process_Shares = DF_Scaling_Factors.pivot_table(values=TechShare_ColName, index=["Activity", "Process"])
    #Process_Shares.to_csv(output_csv_scaling)
    saving3 = Process_Shares.values
    np.savetxt("../Output/CSVs/Scaling1.csv", saving3, delimiter=',')
    
  
    # Fill in any NaNs with 0 in demand (q_System = f)
    # q_System = pd.DataFrame(EndUse_Demand.fillna(0)).drop(selected_resources).sort_index(axis = 0)
    q_System = pd.DataFrame(EndUse_Demand.fillna(0)).sort_index(axis = 0)
    q_System.columns = ['Demand']

    return Process_Coeffs, q_System, Process_Shares
    
     

    