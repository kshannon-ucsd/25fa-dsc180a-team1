# Install poLCA if not already installed
if (!require(poLCA, quietly = TRUE)) {
  install.packages("poLCA")
  library(poLCA)
}

# Read data
data <- read.csv("data/lca_ready_data.csv")
# Prepare LCA data
hadm_ids <- data$hadm_id
lca_data <- data[, !names(data) %in% "hadm_id"]
min_subgroup_size <- ceiling(nrow(lca_data) * 0.05)

# Validate LCA data
validate_data <- function(df, name = "data") {
  # Check missing values
  missing_counts <- colSums(is.na(df))
  if(any(missing_counts > 0)) {
    print(paste("ERROR: Missing values found in", name, ":"))
    print(missing_counts[missing_counts > 0])
    stop("Please handle missing values before running LCA")
  }
  
  # Check constant columns
  var_counts <- sapply(df, function(x) length(unique(x)))
  constant_cols <- var_counts == 1
  if(any(constant_cols)) {
    print(paste("ERROR: Found constant columns in", name, ":"))
    print(names(df)[constant_cols])
    stop("Please remove constant columns before running LCA")
  }
  
  # Check exact number of columns
  if(ncol(df) != 32) {
    print(paste("ERROR: Expected exactly 32 columns, but found", ncol(df), "columns"))
    stop("Data must have exactly 32 columns for LCA")
  }
}
validate_data(lca_data, "LCA data")

# Build formula
formula <- as.formula(paste("cbind(", paste(names(lca_data), collapse = ", "), ") ~ 1"))

# Fit LCA models
fits <- list()
successful_fits <- c()

for(k in 1:8) {
  tryCatch({
    # Use fewer repetitions for testing
    # testing nrep=1, maxiter=500
    # actual nrep = 10, maxiter = 2500
    fit <- poLCA(formula, lca_data, nclass=k, nrep=1, maxiter=1500, verbose=FALSE, na.rm=TRUE)
    fits[[k]] <- fit
    successful_fits <- c(successful_fits, k)
    print(paste("K=", k, ": BIC=", round(fit$bic, 1), ", AIC=", round(fit$aic, 1), sep=""))
  }, error = function(e) {
    print(paste("K=", k, ": Failed -", e$message, sep=""))
    fits[[k]] <- NULL
  })
}

# Create results summary
results_summary <- data.frame(
  K = successful_fits,
  BIC = sapply(successful_fits, function(k) fits[[k]]$bic),
  AIC = sapply(successful_fits, function(k) fits[[k]]$aic),
  MIN_SUBGROUP_SIZE = sapply(successful_fits, function(k) min(table(fits[[k]]$predclass)))
)
write.csv(results_summary, "data/lca_results_summary.csv", row.names = FALSE, quote = FALSE)

# Save subgroup assignments
all_subgroup_assignments <- data.frame(hadm_id = hadm_ids)

for(k in successful_fits) {
  if(!is.null(fits[[k]])) {
    fit <- fits[[k]]
    all_subgroup_assignments[[paste0("subgroup_K", k)]] <- fit$predclass
    all_subgroup_assignments[[paste0("max_prob_K", k)]] <- apply(fit$posterior, 1, max)
  }
}

write.csv(all_subgroup_assignments, "data/lca_all_subgroups.csv", row.names = FALSE, quote = FALSE)
print("✅ All subgroup assignments saved to: data/lca_all_subgroups.csv")

# Find best model
if(length(successful_fits) > 0) {
  # Filter valid models (meeting subgroup size requirements)
  valid_models <- c()
  for(k in successful_fits) {
    if(!is.null(fits[[k]])) {
      subgroup_sizes <- as.numeric(table(fits[[k]]$predclass))
      if(all(subgroup_sizes >= min_subgroup_size)) {
        valid_models <- c(valid_models, k)
      }
    }
  }
  
  if(length(valid_models) > 0) {
    # Find best model among valid models
    valid_results <- results_summary[results_summary$K %in% valid_models, ]
    best_k <- valid_results$K[which.min(valid_results$BIC)]
    best_bic <- valid_results$BIC[valid_results$K == best_k]
    best_aic <- valid_results$AIC[valid_results$K == best_k]
    best_subgroup_sizes <- as.numeric(table(fits[[best_k]]$predclass))
    
    print(paste("\n=== Best Model ==="))
    print(paste("Best model: K =", best_k, "with BIC =", round(best_bic, 1)))
    print(paste("Subgroup sizes:", paste(best_subgroup_sizes, collapse = ", ")))
    
    # Save best model statistics
    best_model_stats <- data.frame(
      best_K = best_k,
      best_BIC = best_bic,
      best_AIC = best_aic,
      min_subgroup_size_required = min_subgroup_size,
      best_model_subgroup_sizes = paste(best_subgroup_sizes, collapse = ", "),
      meets_size_requirement = TRUE,
      total_valid_models = length(valid_models),
      valid_K_values = paste(valid_models, collapse = ", ")
    )
    
  } else {
    print("ERROR: No models meet subgroup size requirements (minimum 5% per subgroup)")
    print(paste("Required minimum subgroup size:", min_subgroup_size))
    print("Available models and their minimum subgroup sizes:")
    for(k in successful_fits) {
      if(!is.null(fits[[k]])) {
        min_size <- min(table(fits[[k]]$predclass))
        print(paste("K =", k, ": minimum subgroup size =", min_size))
      }
    }
    stop("No valid models found - all models have subgroups smaller than 5% threshold")
  }
  
  write.csv(best_model_stats, "data/lca_best_model_stats.csv", row.names = FALSE, quote = FALSE)
}