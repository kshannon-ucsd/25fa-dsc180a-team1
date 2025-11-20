#!/usr/bin/env Rscript
# ===================================================================
# FIGURE 3A – Overall Elixhauser morbidity prevalence (radial barplot)
# ===================================================================

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(tidyr)
  library(ggplot2)
})

# ===================================================================
# 1. LOAD DATA
# ===================================================================

dat_path <- "/Users/varunpabreja/Desktop/dsc180_capstone/25fa-dsc180a-team1/data/lca_data.csv"

df <- read.csv(dat_path, check.names = FALSE)

message("Loaded lca_data: ", nrow(df), " rows.")

# ===================================================================
# 2. DEFINE ELIXHAUSER MORBIDITY COLUMNS (30 VARIABLES)
# ===================================================================

morb_cols <- c(
  "congestive_heart_failure","cardiac_arrhythmias","valvular_disease",
  "pulmonary_circulation","peripheral_vascular","hypertension","paralysis",
  "other_neurological","chronic_pulmonary","diabetes_uncomplicated",
  "diabetes_complicated","hypothyroidism","renal_failure","liver_disease",
  "peptic_ulcer","aids","lymphoma","metastatic_cancer","solid_tumor",
  "rheumatoid_arthritis","coagulopathy","obesity","weight_loss",
  "fluid_electrolyte","blood_loss_anemia","deficiency_anemias",
  "alcohol_abuse","drug_abuse","psychoses","depression"
)

stopifnot(all(morb_cols %in% names(df)))
message("All 30 Elixhauser columns found.")

# ===================================================================
# 3. COMPUTE OVERALL PREVALENCE (%)
# ===================================================================

# Recode to 0/1 for safety: treat NA as 0, any >0 as 1
df_mm <- df %>%
  mutate(
    dplyr::across(
      all_of(morb_cols),
      ~ ifelse(is.na(.), 0L, as.integer(. > 0))
    )
  )

prev_df <- df_mm %>%
  pivot_longer(
    cols      = all_of(morb_cols),
    names_to  = "condition",
    values_to = "value"
  ) %>%
  group_by(condition) %>%
  summarise(
    prevalence = 100 * mean(value, na.rm = TRUE),
    .groups    = "drop"
  )

message("Computed prevalence for ", nrow(prev_df), " conditions.")
# ===================================================================
# 4. BUILD RADIAL BARPLOT (FIG 3A)
# ===================================================================

# Order by prevalence (smallest -> largest) and assign an id for angular position
plot_df <- prev_df %>%
  arrange(prevalence) %>%
  mutate(
    id = dplyr::row_number()
  )

# Add a base radius so all bars start away from the center
base_radius <- 20                       # controls size of the inner hole
plot_df <- plot_df %>%
  mutate(
    r = prevalence + base_radius        # actual radial coordinate
  )

# Radii choices for the plot scale
outer_radius <- max(plot_df$r, na.rm = TRUE) + 15
inner_radius <- 0

# Label positions/angles so text is readable
label_df <- plot_df %>%
  mutate(
    angle = 90 - 360 * (id - 0.5) / n(),
    hjust = ifelse(angle < -90, 1, 0),
    angle = ifelse(angle < -90, angle + 180, angle),
    ylab  = r + 10                      # a bit outside the bar tip
  )

p3a <- ggplot(plot_df, aes(x = factor(id), y = r)) +
  geom_bar(
    stat  = "identity",
    fill  = "grey40",
    color = "white",
    width = 1
  ) +
  coord_polar(start = 0, clip = "off") +
  scale_y_continuous(limits = c(inner_radius, outer_radius)) +
  theme_void() +
  labs(title = "A") +
  theme(
    plot.title  = element_text(size = 24, face = "bold", hjust = 0),
    plot.margin = margin(20, 20, 20, 20)
  ) +
  geom_text(
    data = label_df,
    aes(
      x     = id,
      y     = ylab,
      label = gsub("_", " ", condition),
      angle = angle,
      hjust = hjust
    ),
    size  = 3.2,
    color = "grey20"
  )

print(p3a)

out_path <- "/Users/varunpabreja/Desktop/dsc180_capstone/25fa-dsc180a-team1/data/figure3a_overall_multimorbidity.png"
ggsave(out_path, p3a, width = 9, height = 9, dpi = 300)
message("Saved Fig 3A to: ", out_path)
