library(RnaSeqSampleSize)
library(heatmap3)
library(RColorBrewer)

colors <- colorRampPalette(brewer.pal(9,"Blues"))(100)

args <- commandArgs(trailingOnly = TRUE)
print(args)
mode <- args[1] # data, tcga or none
m <- as.numeric(args[2]) # number of genes
m1 <- as.numeric(args[3]) # expected number of DE genes
n <- as.numeric(args[4]) # sample size
#rho <- as.numeric(args[3]) # minimum detectable log fold change
#lambda0 <- as.numeric(args[5]) # avg. reads
main = "header" # needed, otherwise 'm' screws up the results

if(mode=="none") {
  phi0 <- as.numeric(args[5]) # dispersion
  lambda0 <- as.numeric(args[6]) # avg. read count/gene
  result_file <- args[7]
  result<-optimize_parameter(fun=est_power,main=main,opt1="rho",opt2="f",opt1Value=c(1.1,2,3,4),opt2Value=c(0.01,0.03,0.05,0.1,0.2),m=m,m1=m1,n=n,phi0=phi0,lambda0=lambda0)
}
if(mode=="data") {
  counts_file_path <- args[5]
  tab = read.table(counts_file_path, header=TRUE, sep="\t")
  # only keep read counts
  tab = tab[sapply(tab, is.numeric)]
  counts <- as.matrix(tab[-1,-1])
  dim(counts)
  # if there are less than 1000 genes we need to create more data, as RNASeqSampleSize doesn't work otherwise...
  if(nrow(counts) < 1000) {
    copies <- ceiling(1000/nrow(counts))
    counts <- do.call(rbind, replicate(copies, counts, simplify=FALSE))
  }
  distrObject <- est_count_dispersion(counts)
}
if(mode=="tcga") {
  distrObject <- args[5]
  #data(list = distrObject)
}
if(mode=="tcga" || mode=="data") {
  result_file <- args[6]
  result <- optimize_parameter(fun=est_power_distribution,main=main,opt1="rho",opt2="f",opt1Value=c(1.1,2,3),opt2Value=c(0.01,0.03,0.05,0.1,0.2),m=m, m1=m1,n=n,distributionObject=distrObject)
}
print(result)
pdf(result_file) 
heatmap3(result, Colv = NA, Rowv = NA, xlab = "Minimum detectable log fold change", ylab = "False discovery rate", scale = "n", col = colors, cexCol = 1, cexRow = 1, lasCol = 1, lasRow = 1, main = "Power (sensitivity)")
dev.off()
