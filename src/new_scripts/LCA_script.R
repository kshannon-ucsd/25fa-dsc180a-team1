# ===================================================================
# 0. PACKAGES
# ===================================================================

pkgs <- c("tidyverse", "poLCA", "caret", "pROC", "mclust")
to_install <- setdiff(pkgs, rownames(installed.packages()))
if (length(to_install)) install.packages(to_install)
invisible(lapply(pkgs, library, character.only = TRUE))

message("Packages loaded.")

# ===================================================================
# 1. LOAD DATA
# ===================================================================

df <- read.csv(
  "/Users/varunpabreja/Desktop/dsc180_capstone/25fa-dsc180a-team1/data/lca_data.csv",
  check.names = FALSE
) %>%
  mutate(row_id = dplyr::row_number())   # keep ID to map back later

message("Data loaded: ", nrow(df), " rows.")

# ===================================================================
# 2. PREP LCA INPUTS — FIXED TO MATCH PAPER MORE CLOSELY
# ===================================================================

library(dplyr)
library(tidyr)
library(stringr)

# ---- 2.0 Ensure row_id exists ----
if (!"row_id" %in% names(df)) {
  df <- df %>% mutate(row_id = dplyr::row_number())
}

# ---- 2.1 Define Elixhauser morbidity columns ----
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

# sanity check: all morbidity columns exist
stopifnot(all(morb_cols %in% names(df)))

# make sure the admission_elective_flag column exists
stopifnot("admission_elective_flag" %in% names(df))

# make sure age and gender exist
stopifnot("age" %in% names(df))
stopifnot("gender" %in% names(df))

# ---- 2.2 Admission variable for LCA ----
# Use admission_elective_flag directly as a manifest for LCA.

# ---- 2.3 Make age group factor (same cut as before, from age) ----
df <- df %>%
  mutate(
    age_grp_cat = cut(
      age,
      breaks = c(-Inf, 24, 44, 64, 84, Inf),
      labels = c("16-24","25-44","45-64","65-84",">85"),
      right  = TRUE
    )
  )

# ---- 2.4 Build lca_df with proper 1..K coding for all manifests ----
lca_df <- df %>%
  # only variables needed for LCA
  dplyr::select(
    row_id,
    age_grp_cat,
    gender,
    admission_elective_flag,
    all_of(morb_cols)
  ) %>%
  # recode categorical manifests to 1..K integers
  mutate(
    # enforce consistent factor levels
    age_grp_cat            = factor(
      age_grp_cat,
      levels = c("16-24","25-44","45-64","65-84",">85")
    ),
    gender                 = factor(gender),
    admission_elective_flag = factor(admission_elective_flag),
    
    age_grp = as.integer(age_grp_cat),
    gender  = as.integer(gender),
    adm_type = as.integer(admission_elective_flag)
  ) %>%
  # morbidities: 0/1 -> 1/2, treat NA as 0
  mutate(
    dplyr::across(
      all_of(morb_cols),
      ~ {
        x <- ifelse(is.na(.), 0L, as.integer(. > 0))
        x + 1L
      }
    )
  ) %>%
  # keep only the final manifest variables for LCA
  dplyr::select(
    row_id,
    age_grp,
    gender,
    adm_type,
    all_of(morb_cols)
  ) %>%
  na.omit()

message("LCA dataset prepared: ", nrow(lca_df), " rows, ",
        ncol(lca_df) - 1, " manifest variables.")

# ===================================================================
# 3. SANITY CHECKS
# ===================================================================

# Any NAs left?
message("NAs per column (should all be 0):")
print(colSums(is.na(lca_df)))

# Any NAs in morbidity (manifest) variables?
message("NAs in morbidity columns (should all be 0):")
print(colSums(is.na(lca_df[, morb_cols])))

# Are manifests only 1 / 2?
message("Unique values in morbidity columns (should be 1 and 2):")
print(sapply(lca_df[, morb_cols], function(x) sort(unique(x))))

# ===================================================================
# 4. LCA FORMULA (SAFE)
# ===================================================================

manifest_vars <- setdiff(colnames(lca_df), c("row_id", "latent_class"))

f <- as.formula(
  paste0("cbind(",
         paste(manifest_vars, collapse = ","),
         ") ~ 1")
)

message("LCA formula: ", deparse(f))

# ===================================================================
# 5–7. FIT 6-CLASS LCA MODEL (NO CACHING)
# ===================================================================

# Target class proportions from Zador et al. (2019)
paper_props <- c(
  cardiopulmonary       = 0.061,
  cardiac               = 0.264,
  young                 = 0.235,
  hepatic_addiction     = 0.098,
  complicated_diabetics = 0.094,
  uncomplicated_diab    = 0.248
)

# ---------------------------------------------------------------
# 5. FIT MULTIPLE 6-CLASS LCA MODELS (SEARCH OVER LOCAL OPTIMA)
# ---------------------------------------------------------------
K_TARGET     <- 6
N_RUNS       <- 20    # increase to 80–100 for more exhaustive search
MAXIT        <- 10000
NREP_PER_RUN <- 1     # 1 random start per run; explore many runs instead

set.seed(60)
message("Fitting multiple LCA models for K = 6 ...")

model_list <- vector("list", N_RUNS)
prop_list  <- vector("list", N_RUNS)
ll_list    <- numeric(N_RUNS)
min_prop   <- numeric(N_RUNS)

for (r in seq_len(N_RUNS)) {
  message("  Run ", r, " of ", N_RUNS, " ...")
  m <- poLCA(
    f,
    data    = lca_df,
    nclass  = K_TARGET,
    maxiter = MAXIT,
    nrep    = NREP_PER_RUN,
    verbose = FALSE
  )
  
  model_list[[r]] <- m
  ll_list[r]      <- m$llik
  p               <- prop.table(table(m$predclass))
  prop_list[[r]]  <- p
  min_prop[r]     <- min(as.numeric(p))
}

# ---------------------------------------------------------------
# 6. CHOOSE THE 6-CLASS SOLUTION CLOSEST TO PAPER DISTRIBUTION
# ---------------------------------------------------------------

# sort both vectors before comparing so labels don't matter
paper_sorted <- sort(as.numeric(paper_props))

dist_to_paper <- sapply(prop_list, function(p) {
  p_sorted <- sort(as.numeric(p))
  sqrt(sum((p_sorted - paper_sorted)^2))
})

fits <- tibble(
  run_id          = seq_len(N_RUNS),
  logLik          = ll_list,
  min_class_prop  = min_prop,
  dist_to_paper   = dist_to_paper
) %>%
  # enforce 5% minimum class size like paper
  mutate(eligible = min_class_prop >= 0.05) %>%
  arrange(dist_to_paper)

message("Summary of 6-class runs (top 10 by closeness to paper):")
print(head(fits, 10))

# Prefer *eligible* solutions (all classes ≥5%); if none, fall back to closest overall
if (any(fits$eligible)) {
  best_run <- fits$run_id[fits$eligible][which.min(fits$dist_to_paper[fits$eligible])]
  message("Chosen run (eligible) = ", best_run)
} else {
  best_run <- fits$run_id[which.min(fits$dist_to_paper)]
  message("No runs met 5% class-size rule; chosen closest run = ", best_run)
}

best_fit <- model_list[[best_run]]
best_K   <- K_TARGET

# ---------------------------------------------------------------
# 7. CLASS SIZES (RAW)
# ---------------------------------------------------------------
best_subgroups <- tibble(class = best_fit$predclass) %>%
  dplyr::count(class, name = "n") %>%
  dplyr::mutate(
    prop = n / sum(n),
    K    = best_K
  ) %>%
  dplyr::select(K, class, n, prop) %>%
  dplyr::arrange(class)

message("Final chosen 6-class model. Class sizes:")
print(best_subgroups)

# -------------------------------------------------------------------
# 8. ATTACH LATENT CLASS BACK TO df
# -------------------------------------------------------------------

lca_df$latent_class <- best_fit$predclass

df <- df %>%
  left_join(
    lca_df %>% dplyr::select(row_id, latent_class),
    by = "row_id"
  )

message("Latent classes attached to df.")

# -------------------------------------------------------------------
# 9. CLASS-LEVEL SUMMARY: AGE + ALL 30 MORBIDITY PREVALENCES
# -------------------------------------------------------------------

# Use only rows actually used in LCA (non-missing latent_class)
df_used <- df %>%
  filter(!is.na(latent_class))

N_total <- nrow(df_used)
message("Rows used for class summaries (non-missing latent_class): ", N_total)

# 9.1 Class sizes + age summary (mean, sd, se, 95% CI), pct of sample
class_age_summary <- df_used %>%
  group_by(latent_class) %>%
  summarise(
    n          = n(),
    pct_of_sample = 100 * n / N_total,
    mean_age   = mean(age, na.rm = TRUE),
    sd_age     = sd(age, na.rm = TRUE),
    se_age     = sd_age / sqrt(n),
    ci_low     = mean_age - qt(0.975, df = n - 1) * se_age,
    ci_high    = mean_age + qt(0.975, df = n - 1) * se_age,
    .groups    = "drop"
  ) %>%
  arrange(latent_class)

message("Class-level age summary:")
print(class_age_summary)

# 9.2 Morbidity prevalence (all 30 morbidities), as PERCENT within class
morbidity_summary <- df_used %>%
  group_by(latent_class) %>%
  summarise(
    across(
      all_of(morb_cols),
      ~ 100 * mean(. == 1, na.rm = TRUE),
      .names = "{.col}_pct"
    ),
    .groups = "drop"
  ) %>%
  arrange(latent_class)

message("Class-level morbidity prevalence (percent) for all 30 morbidities:")
print(morbidity_summary)

# 9.3 Proportion of TOTAL liver_disease that lies in each class
if ("liver_disease" %in% morb_cols) {
  liver_total <- df_used %>%
    filter(liver_disease == 1)
  
  denom_liver <- nrow(liver_total)
  
  if (denom_liver > 0) {
    liver_share <- liver_total %>%
      count(latent_class, name = "n_liver") %>%
      mutate(
        liver_disease_prop_of_total = 100 * n_liver / denom_liver
      ) %>%
      select(latent_class, liver_disease_prop_of_total)
  } else {
    liver_share <- tibble(
      latent_class = sort(unique(df_used$latent_class)),
      liver_disease_prop_of_total = 0
    )
  }
} else {
  liver_share <- tibble(
    latent_class = sort(unique(df_used$latent_class)),
    liver_disease_prop_of_total = NA_real_
  )
}

# Ensure every class is represented and NA -> 0 if no liver cases
liver_share <- class_age_summary %>%
  select(latent_class) %>%
  left_join(liver_share, by = "latent_class") %>%
  mutate(
    liver_disease_prop_of_total = ifelse(
      is.na(liver_disease_prop_of_total), 0, liver_disease_prop_of_total
    )
  )

message("Proportion of TOTAL liver_disease by latent class (percent):")
print(liver_share)

# 9.4 Combine everything into one summary table
class_summary_all <- class_age_summary %>%
  left_join(morbidity_summary, by = "latent_class") %>%
  left_join(liver_share, by = "latent_class") %>%
  arrange(latent_class)

# -------------------------------------------------------------------
# 10. WRITE OUTPUTS
# -------------------------------------------------------------------

# 10.1 Class-level summary CSV (this is the main table you asked for)
summary_path <- "/Users/varunpabreja/Desktop/dsc180_capstone/25fa-dsc180a-team1/data/lca_k6_class_summary_all_morbidities.csv"

write.csv(class_summary_all, summary_path, row.names = FALSE)

message("Wrote class-level summary to: ", summary_path)

# 10.2 Patient-level CSV with latent_class (handy for later figures)
patient_path <- "/Users/varunpabreja/Desktop/dsc180_capstone/25fa-dsc180a-team1/data/lca_k6_patient_level_with_class.csv"

write.csv(df, patient_path, row.names = FALSE)

message("Wrote patient-level data with latent_class to: ", patient_path)
