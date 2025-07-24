# The Zero-Emissions Resources (ZER) Calculator, ZER-Calc

**ZER-Calc** is a Python-based model to aggregate energy resource demands of net-zero emissions plans across sectors and industries. All energy demands depend on three Zero Emissions Resources (ZERs): emissions-free electricity, carbon storage and biomass. These aggregated demands for ZERs are calculated by ZER-Calc so they can be compared against estimates of 2050 probable ZER supply. The model is documented in an upcoming paper and its supplementary information (SI) file.

## Requirements

**ZER-Calc** runs on Python version 3.9, using numpy, pandas and matplotlib

## How to use

### Data

The model coefficients are stored in the "Coefficients" sheet of "Recipe_Coefficients.xls". Coefficients are given in the column "Best_Estimate_Data", corresponding to those documented in the SI Part 5 of the upcoming paper. These values can be adjusted.

The model inputs used for the main paper are stored are in the "Demand" and "TechShares" sheets of "Recipe_Coefficients.xls", corresponding to q^ and alpha, descibed in the model maths in the SI Part 2. The values for the model inputs used for the main paper are justified in the SI Part 6. Additional columns can be added to these sheets to consider alternative combinations of net-zero plans.

### To reproduce Figure 2

Clone the repository locally
Use the Jupyter notebook code, "Figure 2.ipynb"

### To reproduce Figure 3

Clone the repository locally
Run the Jupyter notebook code, "Figure 3.ipynb"


## 📌 License

Licensed under MIT Copyright (c) 2025 hawkij

## 📌 Citing

To cite the results, data or approach of the ZER Calculator, please reference our upcoming paper. To cite the model itself, please cite  **Add a citation file here**

---

