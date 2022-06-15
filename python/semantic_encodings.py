# start of file
def preamble(stream, numArgs, numClauses):
    stream.write(('p cnf %i %i\n' %(numArgs, numClauses)).encode())

def neg(a):
    return "-%s" %a
