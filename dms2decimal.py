def dms(d, delim=':', output_string=False):
    """Convert degrees, minutes, seconds to decimal degrees, and back.

    EXAMPLES:

    dms('150:15:32.8')
    dms([7, 49])
    dms(18.235097)
    dms(18.235097, output_string=True)
    
    Also works for negative values.

    SEE ALSO:  :func:`hms`
    """
    # 2008-12-22 00:40 IJC: Created
    # 2009-02-16 14:07 IJC: Works with spaced or colon-ed delimiters
    # 2015-03-19 21:29 IJMC: Copied from phot.py. Added output_string.
    from numpy import sign

    if d.__class__==str or hasattr(d, '__iter__'):   # must be HMS
        if d.__class__==str:
            d = d.split(delim)
            if len(d)==1:
                d = d[0].split(' ')
        s = sign(float(d[0]))
        if s==0:  s=1
        degval = float(d[0])
        if len(d)>=2:
            degval = degval + s*float(d[1])/60.0
        if len(d)==3:
            degval = degval + s*float(d[2])/3600.0
        return degval
    else:    # must be decimal degrees
        if d<0:  
            sgn = -1
        else:
            sgn = +1
        d = abs(d)
        deg = int(d)
        min = int((d-deg)*60.0)
        sec = (d-deg-min/60.0)*3600.0
        ret = (sgn*deg, min, sec)
        if output_string:
            ret = '%+03i:%02i:%04.2f' % ret
        return ret