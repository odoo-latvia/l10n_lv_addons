try:
    from stdnum.exceptions import InvalidChecksum
    from stdnum.lv import pvn
except ImportError:
    pass

def validate(pk):
    """
    Wrap library to preserve old API"""
    try:
        pvn.validate(pk)
    except InvalidChecksum:
        return False
    return True

# fails with 50103591131
#def validate(pk):
#    """
#    Validate a latvian personal identification number
#    or a company registration numnber.
#    Accepts a string with or withouth a '-'.
#    e.g. 000000-00000
#         00000000000
#    """
#    pk = pk.strip()
#    if (not pk.isdigit() or ('-' in pk and len(pk) != 12) 
#            or ('-' not in pk and len(pk) != 11)):
#        return False
#    pk = list(map(int, pk.replace('-', '')))
#    calc = (1 * pk[0]+6* pk[1]+3* pk[2]+7* pk[3]+9* pk[4]+10* pk[5]+5* 
#            pk[6]+8* pk[7]+4* pk[8]+2* pk[9])
#    checksum = (1101- calc)%11;
#    return  checksum ==  pk[10];


