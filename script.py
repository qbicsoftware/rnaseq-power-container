import sys, subprocess, os, configparser

POSTMAN_CONFIG_PATH = "config.txt"
POSTMAN_USER_CONFIG_PATH = "userconfig.txt"
RAW_COUNT_FILE = "raw.read.counts.tsv"
DATA_PATH = "bis_data"
USAGE = '''USAGE

[user] [sampleCode] [app = power/samples] [app parameters...]

power estimation parameters:
power none [# genes] [# diff. expr. genes] [replicates (sample size)] [FDR] [dispersion]
OR
power tcga [# genes] [# diff. expr. genes] [replicates (sample size)] [FDR] [TCGA name]
OR
power data [# genes] [# diff. expr. genes] [replicates (sample size)] [FDR] [code of pilot dataset]

sample size estimation:
samples none [# genes] [# diff expr. genes] [FDR] [dispersion] [avg counts/gene]
OR
samples tcga [# genes] [# diff expr. genes] [FDR] [TCGA name]
OR
samples data [# genes] [# diff expr. genes] [FDR] [code of pilot dataset]'''

def fetchData(app, arguments):
	if(app=="power"):
		code = arguments[5]
	if(app=="samples"):
		code = arguments[4]
	filePath = RAW_COUNT_FILE
	arguments = [a.replace(code, filePath) for a in arguments]

	print("arguments with file:")
	print(arguments)

#	if not os.path.exists(DATA_PATH):
#		os.mkdir(DATA_PATH)
	cpar = configparser.RawConfigParser()
	cpar.read(POSTMAN_USER_CONFIG_PATH)
	pm_user = cpar.get('postman login','user')
	pm_pw = cpar.get('postman login','password')
	cmd = ["java", "-jar", "/postman-cli-0.3.0-custom.jar", code, '@'+POSTMAN_CONFIG_PATH, "-u", pm_user, "-p", pm_pw]
	print(cmd)
	try:
		p = subprocess.Popen(cmd, stdout = subprocess.PIPE)
		p.wait()
		(result, error) = p.communicate()
	except subprocess.CalledProcessError as e:
		sys.stderr.write("common::run_command() : [ERROR]: output = %s, error code = %s\n" % (e.output, e.returncode))
	print("result and errors:")
	print(result)
	print(error)
	return arguments
	
if len(sys.argv) < 4:
	print(USAGE)
	exit()
user = sys.argv[1]
sampleCode = sys.argv[2]
project = sampleCode[0:5]
app = sys.argv[3]
arguments = sys.argv[4:]
source = arguments[0]

if source=="data":
	arguments = fetchData(app, arguments)
	print("arguments again: ")
	print(arguments)
if app=="power":
	filename = "power.pdf"
	cmd = ["Rscript", "/power_matrix.R"] + arguments
elif app=="samples":
	filename = "sample_size.pdf"
	cmd = ["Rscript", "/sample_size_matrix.R"] + arguments
else:
	print(USAGE)
	exit()
cmd += [filename]
print(cmd)

try:
	p = subprocess.Popen(cmd, stdout = subprocess.PIPE)
	p.wait()
	(result, error) = p.communicate()
except subprocess.CalledProcessError as e:
	sys.stderr.write("common::run_command() : [ERROR]: output = %s, error code = %s\n" % (e.output, e.returncode))

print("result of R call:")
print(result)
print("errors: ")
print(error)

#create results folder
results_path = "results"
if not os.path.exists(results_path):
	os.mkdir(results_path)

cmd = ["attachi", "-o", results_path, "-u", user, "-t", "Information", project, filename, "RnaSeqSampleSize analysis for "+project]
print(cmd)

try:
	p = subprocess.Popen(cmd, stdout = subprocess.PIPE)
	p.wait()
	(result, error) = p.communicate()
except subprocess.CalledProcessError as e:
	sys.stderr.write("common::run_command() : [ERROR]: output = %s, error code = %s\n" % (e.output, e.returncode))

print("attachi: ")
print(result)
print("errors: ")
print(error)

listed_dir = os.listdir(results_path)
if len(listed_dir) == 1:
	upload_folder = listed_dir[0]
else:
	sys.exit("folder contains "+len(listed_dir)+" files. existing.")

old_results_path = os.path.join(results_path, upload_folder)
attachCode = project+"000"

cmd = ["sed", "-i", "s/"+attachCode+"/"+sampleCode+"/g", os.path.join(old_results_path, "metadata.txt")]
print(cmd)

try:
	p = subprocess.Popen(cmd, stdout = subprocess.PIPE)
	p.wait()
	(result, error) = p.communicate()
except subprocess.CalledProcessError as e:
	sys.stderr.write("common::run_command() : [ERROR]: output = %s, error code = %s\n" % (e.output, e.returncode))

print("results")
print(result)
print("errors")
print(error)

os.rename(old_results_path, upload_folder)

tar_cmd = ["tar", "-c", upload_folder]
dync_cmd = ["dync", "-n", upload_folder+".tar", "-k", "untar:True", "data.local"]

try:
	tar = subprocess.Popen(tar_cmd, stdout=subprocess.PIPE)
	p = subprocess.Popen(dync_cmd, stdout = subprocess.PIPE, stdin=tar.stdout)
	p.wait()
	(result, error) = p.communicate()
except subprocess.CalledProcessError as e:
	sys.stderr.write("common::run_command() : [ERROR]: output = %s, error code = %s\n" % (e.output, e.returncode))

print("dync results: ")
print(result)
print("errors: ")
print(error)
