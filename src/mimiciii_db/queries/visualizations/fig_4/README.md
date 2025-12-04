# Figure 4 Visualization

This module provides a modular structure for generating Figure 4 visualizations.

## Structure

- **`load_data.py`**: Data loading and merging functions
  - `load_patients_data()`: Load patients from database
  - `load_lca_data()`: Load LCA subgroup assignments
  - `load_sofa_oasis()`: Load SOFA and OASIS scores
  - `load_angus_sepsis()`: Load/create Angus sepsis criteria
  - `merge_all_data()`: Merge all data sources
  - `load_and_merge_all()`: Convenience function to load and merge everything

- **`plot_fig_4_ab.py`**: Panels A & B - SOFA and OASIS boxplots by subgroup
  - `colored_boxplot()`: Helper function for colored boxplots
  - `plot_fig_4_ab()`: Main function to generate panels A & B

- **`plot_fig_4_c.py`**: Panel C - Prevalence of organ dysfunction & sepsis by subgroup
  - `wilson_ci()`: Calculate Wilson confidence intervals
  - `calculate_prevalence_stats()`: Calculate prevalence statistics
  - `plot_fig_4_c()`: Main function to generate panel C

- **`plot_fig_4_d.py`**: Panel D - Conditional mortality by subgroup
  - `wilson_ci()`: Calculate Wilson confidence intervals
  - `calculate_conditional_mortality()`: Calculate conditional mortality stats
  - `plot_fig_4_d()`: Main function to generate panel D

- **`fig_4.py`**: Main orchestration script to generate all panels
- **`4.ipynb`**: Clean notebook that uses the modules interactively

## Usage

### Using the Notebook

```python
from mimiciii_db.queries.visualizations.fig_4 import (
    load_and_merge_all,
    plot_fig_4_ab,
    plot_fig_4_c,
    plot_fig_4_d
)

# Load data
df = load_and_merge_all(db=db)

# Generate panels
plot_fig_4_ab(df, output_path="assets/fig_4/fig_4_ab.png")
plot_fig_4_c(df, output_path="assets/fig_4/fig_4_c.png")
plot_fig_4_d(df, output_path="assets/fig_4/fig_4_d.png")
```

### Using the Script

```bash
python -m mimiciii_db.queries.visualizations.fig_4.fig_4
```

This will generate all panels in `assets/fig_4/`.

## Output Files

- `fig_4_ab.png`: Panels A & B (SOFA and OASIS boxplots)
- `fig_4_c.png`: Panel C (Prevalence)
- `fig_4_d.png`: Panel D (Conditional mortality)

