#!/usr/bin/env Rscript
# Recreate Figure 2:
#   (A) Multimorbidity bubble plot by subgroup (paper classes 1–6)
#   (B) Boxplot of age (years) by subgroup
#
# Uses:
#   - lca_k6_patient_level_with_class.csv
#     (output of the LCA script, with latent_class attached)

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(ggplot2)
  library(tidyr)
})

# ===================================================================
# 1. LOAD PATIENT-LEVEL DATA
# ===================================================================

pat_path <- "/Users/varunpabreja/Desktop/dsc180_capstone/25fa-dsc180a-team1/data/lca_k6_patient_level_with_class.csv"

df <- read.csv(pat_path, check.names = FALSE)

message("Loaded patient-level data: ", nrow(df), " rows.")

# Sanity: ensure latent_class exists
stopifnot("latent_class" %in% names(df))

# ===================================================================
# 2. DEFINE MORBIDITY COLUMNS (SAME 30 ELIXHAUSER VARIABLES)
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

# sanity check: all morbidity columns exist in patient-level data
stopifnot(all(morb_cols %in% names(df)))

# ===================================================================
# 3. MAP latent_class -> PAPER SUBGROUP (1–6)
# ===================================================================
# Mapping you specified:
#  CLASS 1 -> paper CLASS 4 (diabetes_complicated)
#  CLASS 2 -> paper CLASS 5 (diabetes_uncomplicated)
#  CLASS 3 -> paper CLASS 1 (cardiopulmonary)
#  CLASS 4 -> paper CLASS 6 (cardiac)
#  CLASS 5 -> paper CLASS 2 (young)
#  CLASS 6 -> paper CLASS 3 (hepatic_addiction)

mapping_vec <- c(
  `1` = 4,
  `2` = 5,
  `3` = 1,
  `4` = 6,
  `5` = 2,
  `6` = 3
)

df <- df %>%
  mutate(
    subgroup_paper = mapping_vec[as.character(latent_class)],
    subgroup_paper = factor(subgroup_paper, levels = 1:6)
  )

message("Paper-aligned subgroup labels (subgroup_paper) added.")

# Colors by paper subgroup (1..6)
paper_subgroup_colors <- c(
  `1` = "white",   # cardiopulmonary
  `2` = "red",     # young
  `3` = "green",   # hepatic_addiction
  `4` = "blue",    # diabetes_complicated
  `5` = "cyan",    # diabetes_uncomplicated
  `6` = "hotpink"  # cardiac
)

# ===================================================================
# 4. FIGURE 2A – MULTIMORBIDITY BUBBLE PLOT
# ===================================================================

cap <- 8  # 0..7, and ≥8 collapsed into bin 8

df_mm <- df %>%
  filter(!is.na(subgroup_paper)) %>%
  mutate(
    # make sure morbidities are 0/1 here (original scale), then integer
    dplyr::across(
      all_of(morb_cols),
      ~ ifelse(is.na(.), 0L, as.integer(. > 0))
    ),
    morbidity_count = rowSums(dplyr::across(all_of(morb_cols)))
  )

# Frequency per subgroup x binned multimorbidity count
freq <- df_mm %>%
  mutate(mc_binned = pmin(morbidity_count, cap)) %>%
  dplyr::count(subgroup_paper, mc_binned, name = "n")

# Class sizes
class_sizes <- df_mm %>%
  dplyr::count(subgroup_paper, name = "class_n")

# Complete grid (ensure every subgroup & bin appears, even if n=0)
freq <- tidyr::expand_grid(
  subgroup_paper = factor(1:6, levels = 1:6),
  mc_binned      = 0:cap
) %>%
  left_join(freq, by = c("subgroup_paper", "mc_binned")) %>%
  left_join(class_sizes, by = "subgroup_paper") %>%
  mutate(
    n = tidyr::replace_na(n, 0L),
    prop = dplyr::if_else(class_n > 0, n / class_n * 100, 0)
  )

p_multimorb <- ggplot(freq, aes(x = subgroup_paper, y = mc_binned)) +
  # empty circles where prop == 0
  geom_point(
    data = subset(freq, prop == 0),
    shape = 21,
    size = 1.5,
    stroke = 0.4,
    colour = "black",
    fill = NA,
    alpha = 0.6
  ) +
  # filled bubbles where prop > 0
  geom_point(
    data = subset(freq, prop > 0),
    aes(size = prop, fill = subgroup_paper),
    shape = 21,
    colour = "black",
    alpha = 0.85
  ) +
  scale_size_continuous(
    name = "Percent",
    range = c(3, 16),
    breaks = c(10, 20, 30),
    labels = c("10%", "20%", "30%")
  ) +
  scale_fill_manual(
    values = paper_subgroup_colors,
    drop = FALSE,
    guide = "none"
  ) +
  scale_y_continuous(
    breaks = 0:cap,
    labels = c(as.character(0:(cap - 1)), paste0("\u2265", cap))
  ) +
  labs(
    x = "Subgroup",
    y = "Multimorbidity count",
    title = "A"
  ) +
  theme_classic() +
  theme(
    plot.title = element_text(hjust = 0, size = 18, face = "bold"),
    axis.title = element_text(size = 14),
    axis.text = element_text(size = 12),
    panel.grid.major.y = element_line(colour = "grey80", linetype = "dashed"),
    panel.grid.minor = element_blank()
  )

ggsave(
  "/Users/varunpabreja/Desktop/dsc180_capstone/25fa-dsc180a-team1/data/figure2a_multimorbidity_bubble.png",
  p_multimorb,
  width = 5.5,
  height = 5.5,
  dpi = 300
)

message("Saved figure2a_multimorbidity_bubble.png")

# ===================================================================
# 5. FIGURE 2B – AGE (YEARS) BY SUBGROUP
# ===================================================================

df_age <- df %>%
  filter(!is.na(subgroup_paper), !is.na(age))

p_age <- ggplot(df_age, aes(
  x = subgroup_paper,
  y = age,
  fill = subgroup_paper
)) +
  geom_boxplot(
    notch = TRUE,
    outlier.shape = 16,
    outlier.size = 1.5,
    colour = "black",
    width = 0.6
  ) +
  scale_fill_manual(
    values = paper_subgroup_colors,
    drop = FALSE,
    guide = "none"
  ) +
  scale_y_continuous(breaks = c(20, 40, 60, 80, 100)) +
  labs(
    x = "Subgroup",
    y = "Age (years)",
    title = "B"
  ) +
  theme_classic() +
  theme(
    plot.title = element_text(hjust = 0, size = 18, face = "bold"),
    axis.title = element_text(size = 14),
    axis.text = element_text(size = 12),
    panel.grid.major.y = element_line(colour = "grey80", linetype = "dashed"),
    panel.grid.minor = element_blank()
  )

ggsave(
  "/Users/varunpabreja/Desktop/dsc180_capstone/25fa-dsc180a-team1/data/figure2b_age_by_subgroup.png",
  p_age,
  width  = 9,
  height = 5.5,
  dpi = 300
)

message("Saved figure2b_age_by_subgroup.png")
