#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(dendextend)
  library(ComplexHeatmap)
  library(circlize)
})

args_full  <- commandArgs(trailingOnly = FALSE)
file_arg   <- grep("^--file=", args_full, value = TRUE)

script_dir <- if (length(file_arg) > 0) {
  dirname(normalizePath(sub("^--file=", "", file_arg)))
} else {
  "."
}

csv_path <- file.path(script_dir, "..", "..", "..", "..", "..", "..", "data", "heat_matrix_1b.csv")
png_path <- file.path(script_dir, "fig_1b.png")

png(png_path, width = 2200, height = 1400, res = 300)

heat_df <- read.csv(
  csv_path,
  check.names = FALSE, stringsAsFactors = FALSE
)
rownames(heat_df) <- heat_df[[1]]; heat_df[[1]] <- NULL
heat_mat <- as.matrix(heat_df)

grp1 <- c('renal_failure','valvular_disease','hypothyroidism','peripheral_vascular',
          'pulmonary_circulation','chronic_pulmonary',
          'diabetes_uncomplicated','congestive_heart_failure','fluid_electrolyte',
          'hypertension','cardiac_arrhythmias')
grp2 <- c('deficiency_anemias','paralysis','weight_loss','rheumatoid_arthritis',
          'solid_tumor','lymphoma','peptic_ulcer','blood_loss_anemia',
          'psychoses','aids','metastatic_cancer','diabetes_complicated','obesity')
grp3 <- c('other_neurological','coagulopathy','depression','liver_disease',
          'alcohol_abuse','drug_abuse')

present <- intersect(c(grp1, grp2, grp3), rownames(heat_mat))
heat_mat <- heat_mat[present, , drop = FALSE]

block <- factor(
  ifelse(rownames(heat_mat) %in% grp3, "G3",
         ifelse(rownames(heat_mat) %in% grp2, "G2", "G1")),
  levels = c("G3", "G1", "G2")
)

age_order <- c("16-24","25-44","45-64","65-84","≥85")
age_order <- intersect(age_order, colnames(heat_mat))
heat_mat  <- heat_mat[, age_order, drop = FALSE]

col_fun <- colorRamp2(
  c(0, 20, 40, 60, 80),
  c("#0D0D0D", "#FFFF66", "#FFA500", "#FF9000", "#FF3300")
)

method_rows <- "average"
method_cols <- "average"

col_dist <- dist(t(heat_mat), method = "euclidean")
col_hc <- hclust(col_dist, method = method_cols)
col_dend <- as.dendrogram(col_hc)
col_dend_rot <- rotate(col_dend, order = age_order)

ht_rowsplit <- Heatmap(
  heat_mat,
  name = "Prevalence (%)",
  col = col_fun,
  
  row_split = block,
  cluster_rows = TRUE,
  clustering_distance_rows = "euclidean",
  clustering_method_rows = method_rows,
  
  cluster_columns = col_dend_rot,
  column_order = age_order,
  show_row_dend = TRUE,
  show_column_dend = TRUE,
  row_names_side = "left",
  column_names_rot = 45
)

draw(ht_rowsplit)
dev.off()