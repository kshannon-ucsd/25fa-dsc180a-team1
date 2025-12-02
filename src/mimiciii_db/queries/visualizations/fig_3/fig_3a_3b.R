#!/usr/bin/env Rscript
# ===================================================================
# FIGURE 3A & 3B – Elixhauser morbidity prevalence (radial barplots)
# ===================================================================

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(tidyr)
  library(ggplot2)
})

# ===================================================================
# 0. SCRIPT PATHS
# ===================================================================

args_full  <- commandArgs(trailingOnly = FALSE)
file_arg   <- grep("^--file=", args_full, value = TRUE)

script_dir <- if (length(file_arg) > 0) {
  dirname(normalizePath(sub("^--file=", "", file_arg)))
} else {
  "."
}

pat_path <- file.path(
  script_dir,
  "..", "..", "..", "..", "..",
  "data", "lca_k6_patient_level_with_class.csv"
)

out_path_3a <- file.path(
  script_dir, "fig_3a.png"
)

out_path_3b <- file.path(
  script_dir, "fig_3b.png"
)

dir.create(dirname(out_path_3a), recursive = TRUE, showWarnings = FALSE)
dir.create(dirname(out_path_3b), recursive = TRUE, showWarnings = FALSE)

# ===================================================================
# 1. LOAD PATIENT-LEVEL DATA
# ===================================================================

df <- read.csv(pat_path, check.names = FALSE)
message("Loaded patient-level data: ", nrow(df), " rows.")

stopifnot("latent_class" %in% names(df))

# ===================================================================
# 2. DEFINE MORBIDITY COLUMNS
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
message("All 30 Elixhauser columns found in patient-level file.")

# ===================================================================
# 3. MAP latent_class → PAPER SUBGROUP
# ===================================================================

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

paper_subgroup_colors <- c(
  `1` = "grey40",
  `2` = "red",
  `3` = "green",
  `4` = "blue",
  `5` = "cyan",
  `6` = "hotpink"
)

# ===================================================================
# 4. RECODE MORBIDITIES
# ===================================================================

df_mm <- df %>% mutate(
  across(all_of(morb_cols), ~ ifelse(is.na(.), 0L, as.integer(. > 0)))
)

# ===================================================================
# 5. FIGURE 3A – OVERALL PREVALENCE
# ===================================================================

prev_df <- df_mm %>%
  pivot_longer(all_of(morb_cols), names_to = "condition", values_to = "value") %>%
  group_by(condition) %>%
  summarise(prevalence = 100 * mean(value), .groups = "drop")

plot_df <- prev_df %>%
  arrange(prevalence) %>%
  mutate(id = row_number())

base_radius <- 20
plot_df <- plot_df %>% mutate(r = prevalence + base_radius)

outer_radius <- max(plot_df$r) + 15
inner_radius <- 0

label_df <- plot_df %>%
  mutate(
    angle = 90 - 360 * (id - .5) / n(),
    hjust = ifelse(angle < -90, 1, 0),
    angle = ifelse(angle < -90, angle + 180, angle),
    ylab  = r + 10
  )

p3a <- ggplot(plot_df, aes(factor(id), r)) +
  geom_bar(stat = "identity", fill = "grey40", color = "white") +
  coord_polar(start = 0, clip = "off") +
  scale_y_continuous(limits = c(inner_radius, outer_radius)) +
  theme_void() +
  labs(title = "A") +
  theme(plot.title = element_text(size = 24, face = "bold", hjust = 0)) +
  geom_text(
    data = label_df,
    aes(x = id, y = ylab, label = gsub("_", " ", condition),
        angle = angle, hjust = hjust),
    size = 3.2, color = "grey20"
  )

ggsave(out_path_3a, p3a, width = 9, height = 9, dpi = 300)
message("Saved Fig 3A to: ", out_path_3a)

# ===================================================================
# 6. FIGURE 3B – BY SUBGROUP (6 RADIAL PANELS)
# ===================================================================

prev_by_sub <- df_mm %>%
  filter(!is.na(subgroup_paper)) %>%
  pivot_longer(all_of(morb_cols)) %>%
  group_by(subgroup_paper, condition = name) %>%
  summarise(prevalence = 100 * mean(value), .groups = "drop")

plot_df_sub <- prev_by_sub %>%
  group_by(subgroup_paper) %>%
  arrange(prevalence, .by_group = TRUE) %>%
  mutate(id = row_number(), r = prevalence + base_radius) %>%
  ungroup()

outer_radius_sub <- max(plot_df_sub$r) + 15
inner_radius_sub <- 0

label_df_sub <- plot_df_sub %>%
  group_by(subgroup_paper) %>%
  mutate(
    angle = 90 - 360 * (id - .5) / n(),
    hjust = ifelse(angle < -90, 1, 0),
    angle = ifelse(angle < -90, angle + 180, angle),
    ylab  = r + 8
  ) %>%
  ungroup()

p3b <- ggplot(plot_df_sub, aes(factor(id), r, fill = subgroup_paper)) +
  geom_bar(stat = "identity", color = "white", width = 1) +
  coord_polar(start = 0, clip = "off") +
  scale_y_continuous(limits = c(inner_radius_sub, outer_radius_sub)) +
  scale_fill_manual(values = paper_subgroup_colors, guide = "none") +
  facet_wrap(~ subgroup_paper, nrow = 2) +
  theme_void() +
  labs(title = "B") +
  theme(
    plot.title = element_text(size = 24, face = "bold", hjust = 0),
    strip.text = element_text(size = 14, face = "bold")
  ) +
  geom_text(
    data = label_df_sub,
    aes(factor(id), ylab, label = gsub("_", " ", condition),
        angle = angle, hjust = hjust),
    size = 2.5,
    color = "grey20"
  )

ggsave(out_path_3b, p3b, width = 14, height = 8, dpi = 300)
message("Saved Fig 3B to: ", out_path_3b)
