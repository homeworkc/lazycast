import subprocess

p = subprocess.Popen(["./player.bin"],stderr=subprocess.PIPE)

while True:
	#print len(p.stderr)#won't work
	ln = p.stderr.readline()
	print ln

	