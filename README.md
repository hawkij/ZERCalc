# The Zero-Emissions Resources Calculator (ZERCalc)

**ZERCalc** is the open-source Python model accompanying:

Hawkin, J. L. and Allwood, J. M. (2026), “Aggregating Demand for Three Fundamental Resources to Avoid Burden-Shifting in Climate Policy,” Environmental Science & Technology, 60(13), 9958–9972. [https://doi.org/10.1021/acs.est.5c12742](https://doi.org/10.1021/acs.est.5c12742)

The model aggregates the demands that net-zero plans place on three fundamental resources: emissions-free electricity, biomass and carbon storage. It enables these combined demands to be compared with estimates of plausible global supply in 2050, revealing resource competition and potential burden-shifting that may be obscured when mitigation strategies are assessed separately.

## Requirements

**ZERCalc** runs on Python version 3.9. Refer to the file: [pyproject.toml](pyproject.toml) for dependencies.

It is recommended to run the code in a Python virtual environment.

## How to use

### Data

The model coefficients are stored in the "Coefficients" sheet of [Data/Recipe_Coefficients.xls](Data/Recipe_Coefficients.xls). Coefficients are given in the column "Best_Estimate_Data", corresponding to those documented in the SI Part 5 of our published paper [(Hawkin and Allwood 2026)](https://doi.org/10.1021/acs.est.5c12742). These values can be adjusted.

The model inputs used for the published paper [(Hawkin and Allwood 2026)](https://doi.org/10.1021/acs.est.5c12742) are stored in the "Demand" and "TechShares" sheets of [Data/Recipe_Coefficients.xls](Data/Recipe_Coefficients.xls), corresponding to the demand vector, $\hat{q}$, and process shares, $\alpha$, as described in the model maths in the SI Part 2. The values for the model inputs used for the main paper are justified in the SI Part 6. Additional columns can be added to these sheets to consider alternative combinations of net-zero plans.

### To reproduce the timeline, presented as Figure 4 in the final paper

1. Clone the repository locally
2. Change to the 'Code' directory
3. Run the Jupyter notebook code, [Figure 2.ipynb](Code/Figure_2.ipynb)

### To reproduce the feasibility-region analysis, presented as Figure 5 in the final paper

1. Clone the repository locally
2. Change to the 'Code' directory
3. Run the Jupyter notebook code, [Figure 3.ipynb](Code/Figure_3.ipynb)


## License

Licensed under MIT Copyright (c) 2025 hawkij

## Citation

To cite the results, data or approach of the ZER Calculator, please reference [Hawkin, J. L. and Allwood, J. M. (2026)](https://doi.org/10.1021/acs.est.5c12742). To cite the model itself, please use the [ZERCalc citation file](CITATION.cff).

---

