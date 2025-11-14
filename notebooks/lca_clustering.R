#!/usr/bin/env Rscript
suppressPackageStartupMessages({
  library(readr); library(dplyr); library(poLCA); library(ggplot2)
})
set.seed(180)
# ---- Config ----
path <- file.path(getwd(), "data", "lca_ready_data.csv")  # adjust to your actual file name

use_age_bin <- TRUE  # keep categorical age
# ---- Load ----
df <- read_csv(path, show_col_types = FALSE)
names(df) <- make.names(names(df))
# Explicit non-morbidity columns
non_morb <- c("subject_id","hadm_id","age","age_bin","admission_elective_flag")
morb_cols <- setdiff(names(df), non_morb)
# Categorical age column
if (use_age_bin) {
  df$age_bin <- factor(df$age_bin, levels = c("16-24","25-44","45-64","65-84",">=85"))
  age_col <- "age_bin"
} else {
  df$age_disc <- cut(df$age, breaks = c(-Inf,24,44,64,84,Inf),
                     labels = c("16-24","25-44","45-64","65-84",">=85"), right = TRUE)
  age_col <- "age_disc"
}
manifest_vars <- c(age_col, "admission_elective_flag", morb_cols)
# Convert binaries 0/1 -> 1/2 for poLCA (no dplyr helpers)
to12 <- function(x) as.integer(as.numeric(as.character(x))) + 1L
df_lca <- df
df_lca$admission_elective_flag <- to12(df_lca$admission_elective_flag)
df_lca[morb_cols] <- lapply(df_lca[morb_cols], to12)
# Keep only manifest vars & drop NA (base-R to avoid select/all_of)
df_lca <- df_lca[, manifest_vars, drop = FALSE]
df_lca <- stats::na.omit(df_lca)
form <- as.formula(paste0("cbind(", paste(manifest_vars, collapse=","), ") ~ 1"))
# ---- Fit K = 1..10 ----
nrep <- 10;
maxiter <- 5000
fits <- vector("list", 10)
metrics <- tibble(K = 1:10, logLik = NA_real_, df = NA_integer_,
                  AIC = NA_real_, BIC = NA_real_, min_class_pct = NA_real_)
for (K in 1:10) {
  t0 <- Sys.time()
  cat(sprintf("Fitting K = %d\n", K))
  mod <- poLCA(form, data = df_lca, nclass = K,
               nrep = nrep, maxiter = maxiter,
               verbose = FALSE, calc.se = FALSE)
  fits[[K]] <- mod
  metrics$logLik[K] <- mod$llik
  metrics$df[K]     <- mod$npar
  metrics$AIC[K]    <- mod$aic
  metrics$BIC[K]    <- mod$bic
  metrics$min_class_pct[K] <- min(colMeans(mod$posterior))
}
plot_df <- tidyr::pivot_longer(metrics[, c("K","AIC","BIC")],
                               cols = c("AIC","BIC"),
                               names_to = "criterion", values_to = "value")
p <- ggplot(plot_df, aes(x = K, y = value)) +
  geom_line() + geom_point() +
  facet_wrap(~ criterion, scales = "free_y") +
  labs(title = "LCA model selection", x = "K (classes)", y = "Criterion value") +
  theme_minimal(base_size = 13)
print(p)  # In terminal Rscript you may need to run in RStudio or open a device first.
## ==== Final table (rounded + eligibility + winners) ==== ##
# Build a plain data.frame (no dplyr verbs)
metrics_out <- as.data.frame(metrics)
metrics_out$AIC_rounded_10  <- metrics_out$AIC
metrics_out$BIC_rounded_10  <- metrics_out$BIC
metrics_out$min_pct_rounded <- metrics_out$min_class_pct
metrics_out$eligible        <- metrics_out$min_pct_rounded <= 0.05
# Winners among eligible (using ORIGINAL AIC/BIC; the <=0.05 check uses the rounded min pct)
eligible_idx <- which(metrics_out$eligible)
bestAIC_K <- if (length(eligible_idx)) metrics_out$K[eligible_idx[ which.min(metrics_out$AIC[eligible_idx]) ]] else NA_integer_
bestBIC_K <- if (length(eligible_idx)) metrics_out$K[eligible_idx[ which.min(metrics_out$BIC[eligible_idx]) ]] else NA_integer_
metrics_out$best_AIC_under_5pct <- !is.na(bestAIC_K) & metrics_out$K == bestAIC_K
metrics_out$best_BIC_under_5pct <- !is.na(bestBIC_K) & metrics_out$K == bestBIC_K
# Pretty console table via cat/sprintf
cat("\n== Model selection table ==\n")
cat(sprintf("%3s | %10s | %10s | %7s | %8s | %7s | %7s\n",
            "K","AIC(~10)","BIC(~10)","min_pct","eligible","bestAIC","bestBIC"))
cat(paste(rep("-", 72), collapse=""), "\n", sep="")
for (i in seq_len(nrow(metrics_out))) {
  cat(sprintf("%3d | %10.0f | %10.0f | %7.2f | %8s | %7s | %7s\n",
              metrics_out$K[i],
              metrics_out$AIC_rounded_10[i],
              metrics_out$BIC_rounded_10[i],
              metrics_out$min_pct_rounded[i],
              if (metrics_out$eligible[i]) "TRUE" else "FALSE",
              if (metrics_out$best_AIC_under_5pct[i]) "TRUE" else "FALSE",
              if (metrics_out$best_BIC_under_5pct[i]) "TRUE" else "FALSE"))
}
dir.create("outputs", showWarnings = FALSE)
ggsave("outputs/lca_model_selection.png", p, width = 8, height = 5, dpi = 300)
write.csv(metrics_out, "outputs/lca_metrics_table.csv", row.names = FALSE)