# rough Draft
# the age bucket is not correctly assigned
# current performance
[1] "K=1: BIC=729063, AIC=728765.4"
[1] "K=2: BIC=707186.5, AIC=706582.8"
[1] "K=3: BIC=701108.5, AIC=700198.7"
[1] "K=4: BIC=696410.4, AIC=695194.5"
[1] "K=5: BIC=694013.3, AIC=692491.3"
[1] "K=6: BIC=692253.3, AIC=690425.1"
[1] "K=7: BIC=690654.5, AIC=688520.2"
[1] "K=8: BIC=689534.2, AIC=687093.8"


# Install poLCA if not already installed
if (!require(poLCA, quietly = TRUE)) {
  install.packages("poLCA")
  library(poLCA)
}

# Read data
data <- read.csv("temp/lca_data.csv")
print(paste("Data loaded: ", nrow(data), "rows, ", ncol(data), "columns"))

# Check for missing values
print(paste("Missing values per column:"))
print(colSums(is.na(data)))

# Remove rows with any missing values
data <- data[complete.cases(data), ]
print(paste("After removing missing values: ", nrow(data), "rows"))

# Convert all columns to numeric (poLCA requires numeric data)
for(col in names(data)) {
  data[[col]] <- as.numeric(as.factor(data[[col]]))
}

# Check data after conversion
print("Data summary after conversion:")
print(summary(data))

# Check for constant columns (no variation)
constant_cols <- sapply(data, function(x) length(unique(x)) == 1)
if(any(constant_cols)) {
  print("Warning: Found constant columns (no variation):")
  print(names(data)[constant_cols])
  # Remove constant columns
  data <- data[, !constant_cols]
  print(paste("Removed constant columns. New dimensions:", nrow(data), "x", ncol(data)))
}

# Build formula - use all remaining columns
manifest_vars <- names(data)
formula_str <- paste("cbind(", paste(manifest_vars, collapse = ", "), ") ~ 1")
formula <- as.formula(formula_str)
print(paste("Formula:", formula_str))

# Test data suitability for LCA
print("Testing data suitability...")
print(paste("Number of variables:", ncol(data)))
print(paste("Number of observations:", nrow(data)))

# Check if we have enough variation
var_counts <- sapply(data, function(x) length(unique(x)))
print("Number of unique values per variable:")
print(var_counts)

# Only proceed if we have sufficient data
if(nrow(data) < 100) {
  print("ERROR: Too few observations for LCA")
} else if(ncol(data) < 2) {
  print("ERROR: Too few variables for LCA")
} else {
  # Fit LCA models
  fits <- list()
  successful_fits <- c()
  print("Fitting LCA models with K=1 to 8...")
  
  for(k in 1:8) {
    print(paste("  Fitting K=", k, "...", sep=""))
    tryCatch({
      # Use fewer repetitions for testing
      fit <- poLCA(formula, data, nclass=k, nrep=3, maxiter=1000, verbose=FALSE, na.rm=TRUE)
      fits[[k]] <- fit
      successful_fits <- c(successful_fits, k)
      print(paste("    K=", k, ": BIC=", round(fit$bic, 1), ", AIC=", round(fit$aic, 1), sep=""))
    }, error = function(e) {
      print(paste("    K=", k, ": Failed -", e$message, sep=""))
      fits[[k]] <- NULL
    })
  }
}

# Save results
saveRDS(fits, "temp/lca_fits.rds")
print("LCA fitting completed!")

# Print summary of results
print("\n=== LCA Model Summary ===")
print(paste("Successfully fitted models: K =", paste(successful_fits, collapse=", ")))

for(k in successful_fits) {
  if(!is.null(fits[[k]])) {
    print(paste("K=", k, ": BIC=", round(fits[[k]]$bic, 1), ", AIC=", round(fits[[k]]$aic, 1), sep=""))
  }
}

# Find best model based on BIC (lower is better)
if(length(successful_fits) > 0) {
  bic_values <- sapply(successful_fits, function(k) fits[[k]]$bic)
  best_k <- successful_fits[which.min(bic_values)]
  print(paste("\nBest model based on BIC: K =", best_k, "with BIC =", round(fits[[best_k]]$bic, 1)))
}
