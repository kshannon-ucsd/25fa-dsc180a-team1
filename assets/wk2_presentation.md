---
marp: true
theme: gaia
style: |
    .centered-slide {
    display: flex;
    flex-direction: column;
    justify-content: center; /* Vertical centering */
    text-align: center; /* Horizontal centering */
    }

---
<!-- _class: lead -->

# Team 1

Utkarsh, Varun, Gloria, Jason

---
<!-- _class: lead -->

# Basic EDA

- Preliminary results from the paper that we were able to reproduce (almost exactly, with all values lying between the 95% CI):
    - Sample Set (36,607 vs. 36,390)
    - M:F ratio (57.8:42.2 - **EXACTLY RIGHT**)
    - Multimorbidity Percentage (76.8% vs. 77.3%)
    - Overall Mortality Rate (10.82% vs. 10.9%)
---

<!-- _class: lead -->

Utkarsh EDA Plots

---
<!-- _class: lead -->
# Visualizing Plots

- Creating Materialized Views:
    - varun_filtered_patients
    - varun_morbidity_counts
    - varun_filtered_patients_with_morbidity_counts
    - varun_multimorbidity_by_age_bracket_1a

- Using the final MV, and some code in python, we were able to recreate the visualization of Fig 1a:

---
# Figure 1a

<!-- _class: lead -->

![width:20cm height:12.5cm](./visualization_1a.png)

---
# K-Means - II

This is the content of the second slide.

---
# Next Steps

The following week we plan to ...

---